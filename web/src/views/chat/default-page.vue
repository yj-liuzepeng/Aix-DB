<script lang="ts" setup>
import type { UploadFileInfo } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { fetch_datasource_list } from '@/api/datasource'
import { fetch_model_list, set_default_model } from '@/api/aimodel'
import FileUploadManager from '@/views/file/file-upload-manager.vue'

const props = defineProps<{
  collapsed?: boolean
}>()

const emit = defineEmits(['submit'])

const inputValue = ref('')
const selectedMode = ref<{ label: string, value: string, icon: string, color: string } | null>(null)
const datasourceList = ref<any[]>([])
const selectedDatasource = ref<any>(null)
const showDatasourcePopover = ref(false)

// LLM 模型列表（下拉选择）
const llmModels = ref<any[]>([])
const selectedLLMModelId = ref<number | null>(null)

const llmModelOptions = computed(() =>
  llmModels.value.map((m) => ({
    label: m.name,
    value: m.id,
  })),
)

// Dropdown 组件需要的选项格式
const llmModelDropdownOptions = computed(() =>
  llmModels.value.map((m) => ({
    label: () => m.name,
    key: m.id,
  })),
)

// 当前选中模型的名称
const selectedLLMModelName = computed(() => {
  if (!selectedLLMModelId.value) return ''
  const model = llmModels.value.find((m) => m.id === selectedLLMModelId.value)
  return model?.name || ''
})

const loadLLMModels = async () => {
  try {
    const res = await fetch_model_list(undefined, 1)
    const list = Array.isArray(res?.data) ? res.data : Array.isArray(res) ? res : []
    llmModels.value = list
    if (list.length > 0) {
      const defaultItem = list.find((m: any) => m.default_model)
      const model = defaultItem || list[0]
      if (model) {
        selectedLLMModelId.value = model.id
      }
    }
  } catch (e) {
    console.error('加载大语言模型列表失败:', e)
  }
}

// 修改默认大模型（适配 Dropdown 的 select 事件，参数是 key）
const handleLLMModelChange = async (key: number | string) => {
  const modelId = typeof key === 'string' ? parseInt(key) : key
  selectedLLMModelId.value = modelId
  try {
    await set_default_model(modelId)
    window.$ModalMessage?.success?.('默认模型已更新')
  } catch (e) {
    console.error('更新默认模型失败:', e)
    window.$ModalMessage?.error?.('更新默认模型失败，请重试')
  }
}

onMounted(async () => {
  try {
    const res = await fetch_datasource_list()
    if (res.ok) {
      const data = await res.json()
      datasourceList.value = data.data || []
    }
  }
  catch (e) {
    console.error(e)
  }

  // 加载大语言模型列表（用于顶部下拉选择）
  await loadLLMModels()
})

const handleDatasourceSelect = (ds: any) => {
  selectedDatasource.value = ds
  selectedMode.value = chips.find((c) => c.value === 'DATABASE_QA')!
  showDatasourcePopover.value = false
}


// File Upload Logic
const fileUploadRef = ref<InstanceType<typeof FileUploadManager> | null>(null)
const pendingUploadFileInfoList = ref<UploadFileInfo[]>([])

// 检查是否是有效的 Excel 文件
const isValidExcelFile = (file: UploadFileInfo): boolean => {
  const fileName = file.name?.toLowerCase() || ''
  return fileName.endsWith('.xlsx') || fileName.endsWith('.xls') || fileName.endsWith('.csv')
}

// 检查表格问答模式是否满足发送条件
const canSubmitTableQA = computed(() => {
  if (selectedMode.value?.value !== 'FILEDATA_QA') {
    return true // 非表格问答模式，不限制
  }
  
  // 表格问答模式：必须至少有一个已完成的 Excel 文件
  const finishedFiles = pendingUploadFileInfoList.value.filter(
    (f) => f.status === 'finished' && isValidExcelFile(f)
  )
  return finishedFiles.length > 0
})

// 检查是否可以发送（综合判断）
const canSubmit = computed(() => {
  // 基础条件：有文本输入或有文件
  const hasContent = inputValue.value.trim() || pendingUploadFileInfoList.value.length > 0
  
  if (!hasContent) {
    return false
  }
  
  // 表格问答模式特殊检查
  if (selectedMode.value?.value === 'FILEDATA_QA') {
    return canSubmitTableQA.value
  }
  
  return true
})

const handleEnter = (e?: KeyboardEvent) => {
  if (e && e.shiftKey) {
    return
  }

  // 检查是否可以发送
  if (!canSubmit.value) {
    if (selectedMode.value?.value === 'FILEDATA_QA') {
      window.$ModalMessage.warning('表格问答需要上传Excel文件（.xlsx, .xls, .csv）才能发送')
    }
    return
  }

  // Check if files are uploading
  const hasPendingFiles = pendingUploadFileInfoList.value.some((f) => f.status === 'uploading' || (f.status === 'finished' && f.percentage !== 100))
  if (hasPendingFiles) {
    window.$ModalMessage.warning('请等待文件上传完成')
    return
  }

  // Check if files failed
  const hasErrorFiles = pendingUploadFileInfoList.value.some((f) => f.status === 'error')
  if (hasErrorFiles) {
    window.$ModalMessage.warning('存在上传失败的文件，请移除后重试')
    return
  }

  // 表格问答模式：验证文件格式
  if (selectedMode.value?.value === 'FILEDATA_QA') {
    const finishedFiles = pendingUploadFileInfoList.value.filter((f) => f.status === 'finished')
    if (finishedFiles.length === 0) {
      window.$ModalMessage.warning('表格问答需要上传Excel文件（.xlsx, .xls, .csv）才能发送')
      return
    }
    
    const invalidFiles = finishedFiles.filter((f) => !isValidExcelFile(f))
    if (invalidFiles.length > 0) {
      window.$ModalMessage.warning('表格问答只支持Excel文件格式(.xlsx, .xls, .csv)')
      return
    }
  }

  emit('submit', {
    text: inputValue.value,
    mode: selectedMode.value?.value || 'COMMON_QA', // Default to Smart QA if nothing selected
    datasource_id: selectedDatasource.value?.id,
  })
  // We don't clear inputValue here immediately because parent might handle it,
  // but typically we should.
  // However, pendingUploadFileInfoList should probably be cleared by parent or here?
  // Let's clear them here to reset state for next time if we stay on this page (unlikely)
  inputValue.value = ''
  pendingUploadFileInfoList.value = []
  // Clear datasource selection if needed, or keep it? 
  // Requirement says "Input box shows selected datasource", so maybe keep it until cleared.
  // But typically submit resets the input area.
  // Let's reset it for now as we are likely navigating away or resetting the view.
  // selectedDatasource.value = null 
}

const chips = [
  { icon: 'i-hugeicons:ai-chat-02', label: '智能问答', value: 'COMMON_QA', color: '#7E6BF2', placeholder: '先思考后回答，解决更有难度的问题' },
  { icon: 'i-hugeicons:database-01', label: '数据问答', value: 'DATABASE_QA', color: '#10b981', placeholder: '连接数据源，进行自然语言查询' },
  { icon: 'i-hugeicons:table-01', label: '表格问答', value: 'FILEDATA_QA', color: '#f59e0b', placeholder: '上传表格文件，进行数据分析和图表生成' },
  { icon: 'i-hugeicons:search-02', label: '深度搜索', value: 'REPORT_QA', color: '#8b5cf6', placeholder: '输入研究主题，生成深度研究报告' },
]

const placeholderText = computed(() => {
  if (selectedMode.value) {
    const mode = chips.find((c) => c.value === selectedMode.value?.value)
    return mode?.placeholder || '先思考后回答，解决更有难度的问题'
  }
  return '先思考后回答，解决更有难度的问题'
})

const handleChipClick = (chip: typeof chips[0]) => {
  if (chip.value === 'DATABASE_QA') {
    showDatasourcePopover.value = true
    return
  }
  selectedMode.value = chip
  if (chip.value !== 'DATABASE_QA') {
    selectedDatasource.value = null
  }
}

const clearMode = () => {
  // 如果是表格问答模式，清空已上传的文件
  if (selectedMode.value?.value === 'FILEDATA_QA') {
    pendingUploadFileInfoList.value = []
  }
  selectedMode.value = null
  selectedDatasource.value = null
}

const bottomIcons = [
  // Define if needed, or remove if not used in new design
]
</script>

<template>
  <div class="default-page-container">
    <!-- 模型选择：固定在页面左上角，与对话页位置保持一致 -->
    <!-- 当侧边栏折叠时，隐藏此处的模型选择器，因为 top-header 已经显示了 -->
    <div
      v-if="llmModelDropdownOptions.length && !props.collapsed"
      class="model-select-top-left"
    >
      <n-dropdown
        :options="llmModelDropdownOptions"
        placement="bottom-start"
        @select="handleLLMModelChange"
      >
        <div class="model-dropdown-trigger">
          <span class="model-dropdown-label">
            {{ selectedLLMModelName || '选择大语言模型' }}
          </span>
          <div class="model-dropdown-icon i-hugeicons:arrow-down-01"></div>
        </div>
      </n-dropdown>
    </div>

    <div class="content-wrapper">
      <!-- Title -->
      <div class="header-section">
        <div class="logo-wrapper">
          <div class="page-title">
            <span class="gradient-text">A</span>
            <span class="gradient-text i-container">
              i
              <svg
                class="star-icon"
                width="20"
                height="20"
                viewBox="0 0 16 16"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <defs>
                  <linearGradient
                    id="starGradient"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      stop-color="#822dff"
                    />
                    <stop
                      offset="50%"
                      stop-color="#3e45ff"
                    />
                    <stop
                      offset="100%"
                      stop-color="#3ec4fa"
                    />
                  </linearGradient>
                </defs>
                <path
                  d="M8 0L9.5 5.5L15 7L9.5 8.5L8 14L6.5 8.5L1 7L6.5 5.5L8 0Z"
                  fill="url(#starGradient)"
                />
              </svg>
            </span>
            <span class="gradient-text">x</span>
          </div>
        </div>
      </div>

      <!-- Search Box -->
      <div class="input-card">
        <!-- Top: File Uploads -->
        <FileUploadManager
          ref="fileUploadRef"
          v-model="pendingUploadFileInfoList"
          class="w-full"
        />
        
        <!-- 表格问答模式提示：需要上传Excel文件 -->
        <div
          v-if="selectedMode?.value === 'FILEDATA_QA' && !canSubmitTableQA"
          class="table-qa-hint"
        >
          <div class="hint-icon i-hugeicons:info-circle-01"></div>
          <span class="hint-text">表格问答需要上传Excel文件（.xlsx, .xls, .csv）才能发送</span>
        </div>

        <!-- Middle: Input -->
        <div class="input-wrapper w-full">
          <n-input
            v-model:value="inputValue"
            type="textarea"
            :placeholder="placeholderText"
            :autosize="{ minRows: 3, maxRows: 8 }"
            class="custom-input"
            @keydown.enter.prevent="handleEnter"
          />
        </div>

        <!-- Bottom: Footer Actions -->
        <div class="input-footer flex justify-between items-center mt-3">
          <!-- Left: Mode Pill or Chips -->
          <div class="left-actions flex items-center">
            <!-- If mode is selected, show it as a pill -->
            <div
              v-if="selectedMode"
              class="mode-pill"
              :style="{
                color: selectedMode.color,
                borderColor: `${selectedMode.color}30`,
                backgroundColor: `${selectedMode.color}10`,
              }"
            >
              <div
                :class="selectedMode.icon"
                class="text-16"
              ></div>
              <span class="font-medium">{{ selectedMode.label }}</span>
              <span
                v-if="selectedMode.value === 'DATABASE_QA' && selectedDatasource"
                class="font-medium ml-1"
              >
                | {{ selectedDatasource.name }}
              </span>
              <div
                class="i-hugeicons:cancel-01 text-14 ml-1 cursor-pointer opacity-60 hover:opacity-100"
                @click.stop="clearMode"
              ></div>
            </div>

            <!-- If NO mode selected, show chips row inside -->
            <div
              v-else
              class="flex items-center gap-2"
            >
              <template v-for="chip in chips" :key="chip.label">
                <n-popover
                  v-if="chip.value === 'DATABASE_QA'"
                  trigger="click"
                  v-model:show="showDatasourcePopover"
                  placement="bottom"
                  :show-arrow="false"
                  class="!p-0"
                  style="padding: 0;"
                >
                  <template #trigger>
                    <div
                      class="inner-chip"
                      @click="handleChipClick(chip)"
                    >
                      <div
                        :class="chip.icon"
                        class="text-14"
                        :style="{ color: chip.color }"
                      ></div>
                      <span>{{ chip.label }}</span>
                    </div>
                  </template>
                  <div class="flex flex-col min-w-[180px] max-w-[240px] bg-white rounded-xl shadow-2xl border border-gray-100 p-2">
                    <div class="max-h-[320px] overflow-y-auto custom-scrollbar pr-1">
                      <div
                        v-for="ds in datasourceList"
                        :key="ds.id"
                        class="group flex items-center gap-3 px-3 py-2.5 mb-1 last:mb-0 hover:bg-[#F5F3FF] cursor-pointer rounded-lg transition-all duration-200 border border-transparent hover:border-[#DDD6FE]"
                        :class="{ 'bg-[#F5F3FF] border-[#DDD6FE]': selectedDatasource?.id === ds.id }"
                        @click="handleDatasourceSelect(ds)"
                      >
                        <div 
                          class="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-white transition-colors"
                          :class="{ 'bg-white': selectedDatasource?.id === ds.id }"
                        >
                          <div class="i-hugeicons:database-01 text-16 text-gray-400 group-hover:text-[#7E6BF2]" :class="{ 'text-[#7E6BF2]': selectedDatasource?.id === ds.id }"></div>
                        </div>
                        <div class="flex flex-col flex-1 min-w-0">
                          <span class="text-14 text-gray-700 font-semibold group-hover:text-[#7E6BF2] truncate" :class="{ 'text-[#7E6BF2]': selectedDatasource?.id === ds.id }" :title="ds.name">
                            {{ ds.name }}
                          </span>
                          <span class="text-11 text-gray-400 truncate">{{ ds.type || 'Datasource' }}</span>
                        </div>
                        <div v-if="selectedDatasource?.id === ds.id" class="flex-shrink-0">
                          <div class="i-hugeicons:tick-02 text-16 text-[#7E6BF2]"></div>
                        </div>
                      </div>

                      <div v-if="!datasourceList.length" class="flex flex-col items-center justify-center py-10 text-gray-400 gap-2">
                        <div class="i-hugeicons:database-01 text-24 opacity-20"></div>
                        <span class="text-13">暂无可用数据源</span>
                      </div>
                    </div>
                  </div>
                </n-popover>
                <div
                  v-else
                  class="inner-chip"
                  @click="handleChipClick(chip)"
                >
                  <div
                    :class="chip.icon"
                    class="text-14"
                    :style="{ color: chip.color }"
                  ></div>
                  <span>{{ chip.label }}</span>
                </div>
              </template>
            </div>
          </div>

          <!-- Right: Attachment + Send -->
          <div class="right-actions flex items-center gap-3">
            <!-- Attachment (Paperclip) -->
            <n-dropdown
              :options="fileUploadRef?.options || []"
              trigger="click"
              placement="top-end"
            >
              <div class="action-icon i-hugeicons:attachment-01 text-20 text-gray-400 hover:text-gray-600 cursor-pointer"></div>
            </n-dropdown>

            <!-- Send Button (Purple Circle) -->
            <div
              class="send-btn-circle"
              :class="{ disabled: !canSubmit }"
              @click="handleEnter()"
            >
              <div class="i-hugeicons:arrow-up-01 text-white text-20 font-bold"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Removed External Chips Row -->
    </div>
  </div>
</template>

<style scoped lang="scss">
.default-page-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  background-color: #fff;
  position: relative; /* 仅用于定位左上角下拉框，不影响中间内容布局 */
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 900px;
  padding: 0 20px;
  position: relative;
  top: -40px; /* Visual optical adjustment to move slightly up */
}

/* 模型选择下拉框：左上角位置，与对话页面保持一致 */
.model-select-top-left {
  position: absolute;
  top: 12px;
  left: 24px;
  z-index: 10;
}

.header-section {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
  width: 100%;
}

.page-title {
  position: relative;
  display: inline-flex;
  align-items: center;
  font-size: 72px;
  font-weight: 800;
  line-height: 1;
  height: auto;
  margin: 0;
  letter-spacing: -0.04em;
  font-family: "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

.gradient-text {
  background: linear-gradient(135deg, #822dff 0%, #3e45ff 50%, #3ec4fa 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  position: relative;
  z-index: 1;
}

.i-container {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  margin: 0 2px;
}

.star-icon {
  position: absolute;
  top: -12px;
  right: -8px;
  left: auto;
  transform: rotate(15deg);
  filter: drop-shadow(0 0 8px rgba(130, 45, 255, 0.4));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: rotate(15deg) translateY(0); }
  50% { transform: rotate(15deg) translateY(-3px); }
}

/* 模型下拉框样式，使用 Naive UI Dropdown 风格 */
.model-dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 6px;
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.06);
    
    .model-dropdown-icon {
      color: #6b7280;
    }
  }
}

.model-dropdown-label {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.4;
  letter-spacing: -0.01em;
  font-family: "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.model-dropdown-icon {
  font-size: 14px;
  color: #9ca3af;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Input Card Styles matching chat.vue */

.input-card {
  width: 100%;
  max-width: 890px;
  background-color: #fff;
  border-radius: 24px;
  box-shadow: 0 10px 40px -10px rgb(0 0 0 / 8%);
  border: 1px solid #f1f5f9;
  padding: 24px;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    box-shadow: 0 20px 50px -12px rgb(0 0 0 / 12%);
    border-color: #e2e8f0;
    transform: translateY(-2px);
  }
}

.input-wrapper {
  width: 100%;
  margin: 8px 0;
}

.custom-input {
  --n-border: none !important;
  --n-border-hover: none !important;
  --n-border-focus: none !important;
  --n-box-shadow: none !important;
  --n-box-shadow-focus: none !important;

  background-color: transparent !important;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.625;
  letter-spacing: 0;
  padding: 0;
  flex: 1;

  :deep(.n-input__textarea-el) {
    padding: 0;
    min-height: 80px;
    line-height: 1.625;
    color: #1a1a1a;
    font-size: 16px;
    font-weight: 400;
    letter-spacing: 0;
  }

  :deep(.n-input__placeholder) {
    color: #94a3b8;
  }
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.mode-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.5;
  letter-spacing: 0.01em;
  border: 1px solid transparent;
  transition: all 0.2s;
  cursor: default;
}

.inner-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.5;
  letter-spacing: 0.01em;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  background-color: #f8fafc;
  border: 1px solid transparent;

  &:hover, &.active-chip {
    background-color: #f1f5f9;
    color: #334155;
    border-color: #e2e8f0;
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}

.action-icon {
  font-size: 20px;
  color: #6b7280;
  cursor: pointer;
  transition: color 0.2s;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;

  &:hover {
    color: #374151;
  }
}

.send-btn-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #7E6BF2;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgb(126 107 242 / 30%);

  &:hover:not(.disabled) {
    background-color: #6b5ae0;
    transform: scale(1.05);
  }

  &.disabled {
    background-color: #e5e7eb;
    cursor: not-allowed;
    box-shadow: none;
    opacity: 0.6;

    .i-hugeicons:arrow-up-01 {
      color: #9ca3af;
    }
  }
}

/* 表格问答模式提示样式 */
.table-qa-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-top: 8px;
  background-color: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 8px;
  font-size: 13px;
  color: #92400e;
  
  .hint-icon {
    font-size: 16px;
    color: #f59e0b;
    flex-shrink: 0;
  }
  
  .hint-text {
    line-height: 1.4;
    flex: 1;
  }
}
</style>
