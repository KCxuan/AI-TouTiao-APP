<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getCategories, publishNews, updateNews, getMyNewsList } from '../api/news'
import { toast } from '../composables/toast'

const router = useRouter()
const route = useRoute()

// 编辑模式：路由带 ?edit=<新闻ID> 时进入（由"我的发布"页跳转而来）
const editId = computed(() => Number(route.query.edit) || null)
const isEdit = computed(() => editId.value !== null)

const categories = ref([])
const loadingCategories = ref(true)
const publishing = ref(false)
const errorMsg = ref('')

const form = reactive({
  categoryId: null,
  title: '',
  description: '',
  image: '',
  content: ''
})

// 编辑模式回填表单：优先取"我的发布"页存入 sessionStorage 的文章数据（含全部 ORM 字段），
// 刷新丢失时回退到拉取我的发布列表查找（详情接口不含 description，故不用它）
async function loadArticleForEdit(id) {
  let item = null
  try {
    const cached = JSON.parse(sessionStorage.getItem('toutiao_edit_news') || 'null')
    if (cached && Number(cached.id) === id) {
      item = cached
    }
  } catch (e) {
    /* sessionStorage 数据损坏时走回退逻辑 */
  }
  if (!item) {
    try {
      const body = await getMyNewsList(1, 100)
      item = (body.data?.list || []).find((n) => Number(n.id) === id) || null
    } catch (e) {
      /* 拉取失败按未找到处理 */
    }
  }
  if (!item) {
    toast('未找到待编辑的文章，请从"我的发布"重新进入', 'error')
    router.replace('/mine')
    return
  }
  form.categoryId = item.category_id
  form.title = item.title || ''
  form.description = item.description || ''
  form.image = item.image || ''
  form.content = item.content || ''
}

onMounted(async () => {
  try {
    const body = await getCategories()
    categories.value = body.data || []
    // 默认选中第一个分类，避免"未选择"状态
    if (categories.value.length > 0 && !isEdit.value) {
      form.categoryId = categories.value[0].id
    }
    if (isEdit.value) {
      await loadArticleForEdit(editId.value)
    }
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loadingCategories.value = false
  }
})

// 前端先按后端约束挡一层（后端 NewsCreateRequest 校验兜底）
function validate() {
  if (!form.categoryId) {
    return '请选择新闻分类'
  }
  const title = form.title.trim()
  if (title.length < 1) {
    return '请填写新闻标题'
  }
  if (title.length > 255) {
    return '标题不能超过 255 个字符'
  }
  if (form.description.length > 500) {
    return '简介不能超过 500 个字符'
  }
  if (!form.content.trim()) {
    return '请填写新闻内容'
  }
  if (form.image.length > 255) {
    return '封面图片 URL 不能超过 255 个字符'
  }
  return ''
}

async function handleSubmit() {
  errorMsg.value = ''
  const invalid = validate()
  if (invalid) {
    errorMsg.value = invalid
    return
  }

  publishing.value = true
  try {
    if (isEdit.value) {
      // 编辑模式：提交全部字段（后端按传入字段部分更新）
      const body = await updateNews({
        id: editId.value,
        categoryId: form.categoryId,
        title: form.title.trim(),
        description: form.description.trim(),
        image: form.image.trim(),
        content: form.content
      })
      sessionStorage.removeItem('toutiao_edit_news')
      toast(body.message || '更新成功', 'success')
      router.push(`/news/${editId.value}`)
    } else {
      const body = await publishNews({
        categoryId: form.categoryId,
        title: form.title.trim(),
        description: form.description.trim(),
        image: form.image.trim(),
        content: form.content
      })
      toast(body.message || '发布成功', 'success')
      // 跳转到新文章详情页（响应 data 为 ORM snake_case，id 即新闻ID）
      router.push(`/news/${body.data.id}`)
    }
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    publishing.value = false
  }
}
</script>

<template>
  <div class="container publish-page">
    <div class="page-head">
      <h1 class="page-title">{{ isEdit ? '编辑新闻' : '发布新闻' }}</h1>
      <p class="page-sub">
        {{
          isEdit
            ? '修改后保存，相关缓存会自动刷新'
            : '发布成功后，文章会立即出现在对应分类的列表中'
        }}
      </p>
    </div>

    <div class="card form-card">
      <div v-if="loadingCategories" class="loading-block" style="padding: 32px 0">
        <span class="loading-spinner"></span>
        <p>正在加载分类…</p>
      </div>

      <form v-else @submit.prevent="handleSubmit">
        <div class="field">
          <label for="category">分类 <span class="required">*</span></label>
          <select id="category" v-model.number="form.categoryId">
            <option v-if="categories.length === 0" :value="null" disabled>
              暂无分类（请先在数据库 news_category 表中添加）
            </option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>
        </div>

        <div class="field">
          <label for="title">
            标题 <span class="required">*</span>
            <span class="char-count">{{ form.title.length }}/255</span>
          </label>
          <input
            id="title"
            v-model="form.title"
            type="text"
            placeholder="请输入新闻标题"
            maxlength="255"
          />
        </div>

        <div class="field">
          <label for="description">
            简介
            <span class="char-count">{{ form.description.length }}/500</span>
          </label>
          <textarea
            id="description"
            v-model="form.description"
            placeholder="一句话概括这篇新闻（选填，会显示在列表卡片上）"
            maxlength="500"
          ></textarea>
        </div>

        <div class="field">
          <label for="image">封面图片 URL</label>
          <input
            id="image"
            v-model="form.image"
            type="text"
            placeholder="https://…（选填，图片链接）"
            maxlength="255"
          />
        </div>

        <div class="field">
          <label for="content">正文 <span class="required">*</span></label>
          <textarea
            id="content"
            v-model="form.content"
            class="content-input"
            placeholder="请输入新闻正文…"
          ></textarea>
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" @click="router.back()">
            取消
          </button>
          <button type="submit" class="btn btn-primary" :disabled="publishing">
            {{ publishing ? (isEdit ? '保存中…' : '发布中…') : isEdit ? '保存修改' : '发布新闻' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.publish-page {
  max-width: 760px;
}

.page-head {
  margin-bottom: 20px;
}

.page-sub {
  font-size: 13.5px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.form-card {
  padding: 32px 36px;
}

.required {
  color: var(--accent);
}

.char-count {
  float: right;
  font-weight: 400;
  color: var(--text-tertiary);
  font-size: 12px;
}

.content-input {
  min-height: 260px;
  line-height: 1.8;
}

.error-msg {
  background-color: var(--error-soft);
  color: var(--error);
  font-size: 13px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}
</style>
