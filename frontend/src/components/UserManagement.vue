<template>
  <div class="user-management">
    <div class="container">
      <div class="header">
        <h2>User Management</h2>
        <button @click="showCreateModal = true" class="btn btn-primary">
          <i class="fas fa-plus"></i> Create User
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading && users.length === 0" class="loading-state">
        <div class="spinner"></div>
        <p>Loading users...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!loading && users.length === 0" class="empty-state">
        <div class="empty-icon">
          <i class="fas fa-users"></i>
        </div>
        <h3>No Users Found</h3>
        <p>Get started by creating your first user account.</p>
        <button @click="showCreateModal = true" class="btn btn-primary">
          <i class="fas fa-plus"></i> Create First User
        </button>
      </div>

      <!-- Users Table -->
      <div v-else class="users-table">
        <div class="table-header">
          <h3>All Users ({{ users.length }})</h3>
          <div class="table-actions">
            <button @click="fetchUsers" class="btn btn-outline btn-sm" :disabled="loading">
              <i class="fas fa-refresh"></i> Refresh
            </button>
          </div>
        </div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>
                  <div class="user-info">
                    <strong>{{ user.username }}</strong>
                    <span v-if="user.id === currentUser?.id" class="current-user-badge">You</span>
                    <span v-if="user.is_system_admin" class="system-admin-badge">System Admin</span>
                  </div>
                </td>
                <td>{{ user.full_name }}</td>
                <td>{{ user.email }}</td>
                <td>
                  <span :class="getRoleClass(user.role)">
                    {{ formatRole(user.role) }}
                  </span>
                </td>
                <td>
                  <span :class="user.is_active ? 'status-active' : 'status-inactive'">
                    {{ user.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <div class="action-buttons">
                    <button @click="editUser(user)" class="btn btn-sm btn-outline" title="Edit User">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button 
                      @click="deleteUser(user)" 
                      class="btn btn-sm btn-danger"
                      :disabled="user.id === currentUser?.id || user.is_system_admin"
                      :title="user.id === currentUser?.id ? 'Cannot delete yourself' : user.is_system_admin ? 'Cannot delete system administrator' : 'Delete User'"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Create User Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Create New User</h3>
          <button @click="closeCreateModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createUser">
            <div class="form-group">
              <label>Username *</label>
              <input 
                type="text" 
                v-model="newUser.username" 
                required 
                :class="{ 'error': errors.username }"
              >
              <span v-if="errors.username" class="error-text">{{ errors.username }}</span>
            </div>
            
            <div class="form-group">
              <label>Full Name *</label>
              <input 
                type="text" 
                v-model="newUser.full_name" 
                required 
                :class="{ 'error': errors.full_name }"
              >
              <span v-if="errors.full_name" class="error-text">{{ errors.full_name }}</span>
            </div>
            
            <div class="form-group">
              <label>Email *</label>
              <input 
                type="email" 
                v-model="newUser.email" 
                required 
                :class="{ 'error': errors.email }"
              >
              <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
            </div>
            
            <div class="form-group">
              <label>Password *</label>
              <input 
                type="password" 
                v-model="newUser.password" 
                required 
                :class="{ 'error': errors.password }"
              >
              <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
            </div>
            
            <div class="form-group">
              <label>Role *</label>
              <select v-model="newUser.role" required>
                <option value="visitor">Visitor</option>
                <option value="executive">Executive</option>
                <option value="operator">Operator</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="closeCreateModal" class="btn btn-secondary">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="loading">
                {{ loading ? 'Creating...' : 'Create User' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Edit User Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Edit User</h3>
          <button @click="closeEditModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="updateUser">
            <div class="form-group">
              <label>Username</label>
              <input 
                type="text" 
                v-model="editingUser.username" 
                :class="{ 'error': errors.username }"
                :disabled="editingUser.is_system_admin"
                :title="editingUser.is_system_admin ? 'System administrator username cannot be changed (set via environment)' : ''"
              >
              <span v-if="errors.username" class="error-text">{{ errors.username }}</span>
              <span v-if="editingUser.is_system_admin" class="info-text">
                <i class="fas fa-info-circle"></i> Username is set via environment variables and cannot be changed
              </span>
            </div>
            
            <div class="form-group">
              <label>Full Name</label>
              <input 
                type="text" 
                v-model="editingUser.full_name" 
                :class="{ 'error': errors.full_name }"
              >
              <span v-if="errors.full_name" class="error-text">{{ errors.full_name }}</span>
            </div>
            
            <div class="form-group">
              <label>Email</label>
              <input 
                type="email" 
                v-model="editingUser.email" 
                :class="{ 'error': errors.email }"
              >
              <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
            </div>
            
            <div class="form-group">
              <label>New Password (leave blank to keep current)</label>
              <input 
                type="password" 
                v-model="editingUser.password" 
                :class="{ 'error': errors.password }"
                :disabled="editingUser.is_system_admin"
                :title="editingUser.is_system_admin ? 'System administrator password cannot be changed (set via environment)' : ''"
              >
              <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
              <span v-if="editingUser.is_system_admin" class="info-text">
                <i class="fas fa-info-circle"></i> Password is set via environment variables and cannot be changed
              </span>
            </div>
            
            <div class="form-group">
              <label>Role</label>
              <select v-model="editingUser.role">
                <option value="visitor">Visitor</option>
                <option value="executive">Executive</option>
                <option value="operator">Operator</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>
                <input type="checkbox" v-model="editingUser.is_active">
                Active
              </label>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="closeEditModal" class="btn btn-secondary">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="loading">
                {{ loading ? 'Updating...' : 'Update User' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

export default {
  name: 'UserManagement',
  setup() {
    const authStore = useAuthStore()
    
    // Create a dedicated axios instance for user management
    const API_BASE_URL = import.meta.env.VITE_API_URL || 
      (window.location.origin.includes('localhost') ? 'http://localhost:8003' : window.location.origin)
    
    const api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    // Add auth token interceptor
    api.interceptors.request.use((config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    
    const users = ref([])
    const loading = ref(false)
    const showCreateModal = ref(false)
    const showEditModal = ref(false)
    const errors = ref({})
    
    const newUser = ref({
      username: '',
      full_name: '',
      email: '',
      password: '',
      role: 'visitor'
    })
    
    const editingUser = ref({})
    
    const currentUser = computed(() => authStore.user)
    
    const fetchUsers = async () => {
      try {
        loading.value = true
        console.log('Fetching users...')
        
        const response = await api.get('/api/auth/users')
        console.log('Users response:', response.data)
        
        if (response.data.success) {
          users.value = response.data.users || []
        } else {
          console.error('Failed to fetch users:', response.data.message)
          alert('Failed to fetch users: ' + response.data.message)
        }
      } catch (error) {
        console.error('Error fetching users:', error)
        console.error('Error details:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message
        })
        
        // Only show error if it's not a 401 (unauthorized) 
        if (error.response?.status !== 401) {
          const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message
          alert('Failed to fetch users: ' + errorMessage)
        }
      } finally {
        loading.value = false
      }
    }
    
    const createUser = async () => {
      try {
        loading.value = true
        errors.value = {}
        
        const response = await api.post('/api/auth/users', newUser.value)
        
        if (response.data.success) {
          alert('User created successfully!')
          await fetchUsers()
          closeCreateModal()
        } else {
          alert(response.data.message || 'Failed to create user')
        }
      } catch (error) {
        console.error('Error creating user:', error)
        if (error.response?.data?.detail) {
          // Handle validation errors
          if (Array.isArray(error.response.data.detail)) {
            error.response.data.detail.forEach(err => {
              errors.value[err.loc[1]] = err.msg
            })
          } else {
            alert(error.response.data.detail)
          }
        } else {
          alert('Failed to create user: ' + (error.response?.data?.message || error.message))
        }
      } finally {
        loading.value = false
      }
    }
    
    const editUser = (user) => {
      editingUser.value = {
        id: user.id,
        username: user.username,
        full_name: user.full_name,
        email: user.email,
        password: '',
        role: user.role,
        is_active: user.is_active,
        is_system_admin: user.is_system_admin || false
      }
      showEditModal.value = true
    }
    
    const updateUser = async () => {
      try {
        loading.value = true
        errors.value = {}
        
        const updateData = { ...editingUser.value }
        if (!updateData.password) {
          delete updateData.password // Don't send empty password
        }
        delete updateData.id
        
        const response = await api.put(`/api/auth/users/${editingUser.value.id}`, updateData)
        
        if (response.data.success) {
          alert('User updated successfully!')
          await fetchUsers()
          closeEditModal()
        } else {
          alert(response.data.message || 'Failed to update user')
        }
      } catch (error) {
        console.error('Error updating user:', error)
        if (error.response?.data?.detail) {
          if (Array.isArray(error.response.data.detail)) {
            error.response.data.detail.forEach(err => {
              errors.value[err.loc[1]] = err.msg
            })
          } else {
            alert(error.response.data.detail)
          }
        } else {
          alert('Failed to update user: ' + (error.response?.data?.message || error.message))
        }
      } finally {
        loading.value = false
      }
    }
    
    const deleteUser = async (user) => {
      if (!confirm(`Are you sure you want to delete user "${user.username}"?`)) {
        return
      }
      
      try {
        loading.value = true
        const response = await api.delete(`/api/auth/users/${user.id}`)
        
        if (response.data.success) {
          alert('User deleted successfully!')
          await fetchUsers()
        } else {
          alert(response.data.message || 'Failed to delete user')
        }
      } catch (error) {
        console.error('Error deleting user:', error)
        alert('Failed to delete user: ' + (error.response?.data?.detail || error.message))
      } finally {
        loading.value = false
      }
    }
    
    const closeCreateModal = () => {
      showCreateModal.value = false
      newUser.value = {
        username: '',
        full_name: '',
        email: '',
        password: '',
        role: 'visitor'
      }
      errors.value = {}
    }
    
    const closeEditModal = () => {
      showEditModal.value = false
      editingUser.value = {}
      errors.value = {}
    }
    
    const getRoleClass = (role) => {
      const classes = {
        admin: 'role-admin',
        operator: 'role-operator',
        executive: 'role-executive',
        visitor: 'role-visitor'
      }
      return classes[role] || 'role-visitor'
    }
    
    const formatRole = (role) => {
      return role.charAt(0).toUpperCase() + role.slice(1)
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }
    
    onMounted(() => {
      fetchUsers()
    })
    
    return {
      users,
      loading,
      showCreateModal,
      showEditModal,
      errors,
      newUser,
      editingUser,
      currentUser,
      fetchUsers,
      createUser,
      editUser,
      updateUser,
      deleteUser,
      closeCreateModal,
      closeEditModal,
      getRoleClass,
      formatRole,
      formatDate
    }
  }
}
</script>

<style scoped>
.user-management {
  min-height: 100vh;
  background-color: #f8f9fa;
  padding: 1rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header h2 {
  margin: 0;
  color: #333;
  font-size: 1.8rem;
}

.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.empty-icon {
  font-size: 4rem;
  color: #6c757d;
  margin-bottom: 1rem;
}

.empty-state h3 {
  color: #333;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #6c757d;
  margin-bottom: 2rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
  transform: translateY(-1px);
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-outline {
  background-color: transparent;
  border: 1px solid #007bff;
  color: #007bff;
}

.btn-outline:hover {
  background-color: #007bff;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.users-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  background-color: #f8f9fa;
}

.table-header h3 {
  margin: 0;
  color: #333;
}

.table-actions {
  display: flex;
  gap: 0.5rem;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background-color: #fff;
  font-weight: 600;
  color: #495057;
  position: sticky;
  top: 0;
}

tr:hover {
  background-color: #f8f9fa;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.current-user-badge {
  background-color: #007bff;
  color: white;
  padding: 0.125rem 0.375rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
}

.system-admin-badge {
  background-color: #6f42c1;
  color: white;
  padding: 0.125rem 0.375rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
  margin-left: 0.25rem;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.role-admin {
  background-color: #dc3545;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.role-operator {
  background-color: #fd7e14;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.role-executive {
  background-color: #20c997;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.role-visitor {
  background-color: #6c757d;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-active {
  color: #28a745;
  font-weight: 600;
}

.status-inactive {
  color: #dc3545;
  font-weight: 600;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  background-color: #f8f9fa;
  border-radius: 12px 12px 0 0;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #333;
  background-color: #e9ecef;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
}

.form-group input.error,
.form-group select.error {
  border-color: #dc3545;
}

.error-text {
  color: #dc3545;
  font-size: 0.8rem;
  margin-top: 0.25rem;
  display: block;
}

.info-text {
  color: #6c757d;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  display: block;
  font-style: italic;
}

.info-text i {
  margin-right: 0.25rem;
}

.form-group input:disabled,
.form-group select:disabled {
  background-color: #f8f9fa;
  color: #6c757d;
  cursor: not-allowed;
  opacity: 0.8;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

input[type="checkbox"] {
  width: auto !important;
  margin-right: 0.5rem;
}

/* Responsive */
@media (max-width: 768px) {
  .user-management {
    padding: 0.5rem;
  }
  
  .header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .table-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  th, td {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
  
  .modal {
    margin: 1rem;
    max-width: none;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>
