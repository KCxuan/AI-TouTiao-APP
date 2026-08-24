import request from './request'

// ===== 用户模块 =====

// 用户注册：成功返回 { token, userInfo }
export function registerUser(data) {
  return request.post('/api/user/register', {
    username: data.username,
    password: data.password
  })
}

// 用户登录：成功返回 { token, userInfo }
export function loginUser(data) {
  return request.post('/api/user/login', {
    username: data.username,
    password: data.password
  })
}

// 获取当前登录用户信息
export function getUserInfo() {
  return request.get('/api/user/info')
}

// 更新用户信息（nickname/avatar/gender/bio/phone 均可选）
export function updateUserInfo(data) {
  return request.put('/api/user/update', {
    nickname: data.nickname,
    avatar: data.avatar,
    gender: data.gender,
    bio: data.bio,
    phone: data.phone
  })
}

// 修改密码
export function changePassword(oldPassword, newPassword) {
  return request.put('/api/user/password', {
    oldPassword,
    newPassword
  })
}
