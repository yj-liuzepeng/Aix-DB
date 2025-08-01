<!-- ToolAgent.vue -->
<template>
  <n-layout class="main-layout" style="height: 100vh">
    <div class="tool-agent">
      <div class="chat-container">
        <div class="messages">
          <div 
            v-for="message in messages" 
            :key="message.id"
            :class="['message', message.role]"
          >
            <div v-if="message.role === 'user'"  class="content">
              {{ message.content }}
            </div>
             <div v-else-if="message.role === 'assistant'" class="content">
              <div class="markdown-wrapper" v-html="renderedMarkdown(message.content || '')"></div>
            </div>
            <div v-else-if="message.role === 'tool'" class="content">
              <strong>工具执行结果:</strong> {{ message.content }}
            </div>
            <div v-if="message.tool_calls" class="tool-calls">
              <div 
                v-for="toolCall in message.tool_calls" 
                :key="toolCall.id"
                class="tool-call"
              >
                调用工具: {{ toolCall.function.name }} 
                参数: {{ toolCall.function.arguments }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="input-area">
          <input 
            v-model="userInput" 
            @keyup.enter="sendMessage"
            placeholder="输入消息..."
            :disabled="loading"
          />
          <button @click="sendMessage" :disabled="loading">
            {{ loading ? '处理中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js'
import MarkdownInstance from '../../components/MarkdownPreview/plugins/markdown'


// 添加 Markdown 渲染计算函数
const renderedMarkdown = (content: string) => {
  return MarkdownInstance.render(content)
}


const transport = new SSEClientTransport(
  new URL(`${location.origin}/sse`),
)

const client = new Client(
  {
    name: 'mcp-client',
    version: '1.0.0',
  },
  {
    capabilities: {
      prompts: {},
      resources: {},
      tools: {},
    },
  },
)

// 消息类型定义
interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content?: string
  tool_calls?: ToolCall[]
  tool_call_id?: string
}

interface ToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
}

interface Tool {
    name: string
    description?: string
    inputSchema?: any
}

// 响应式数据
const availableTools = ref<Tool[]>([])
const messages = ref<Message[]>([])
const userInput = ref('')
const loading = ref(false)

// 初始化连接
onMounted(async () => {
  await client.connect(transport)
  const tools = await client.listTools()
  console.log(tools)
  availableTools.value = tools.tools.map(tool => ({
    name: tool.name,
    description: tool.description,
    inputSchema: tool.inputSchema
  }))
})

// 调用工具
const callTool = async (toolName: string, parameters: any) => {
   const result = await client.callTool({
    name: toolName,
    arguments: parameters
   })
  return result.content
}


// 调用通义千问API
const callLLM = async (messages: Message[], tools: Tool[]): Promise<any> => {
  try {
    const userMessage = [{
      role: 'user',
      content: userInput.value
    }, {
      role: 'system',
      content: `
      你现在可以使用一系列强大的工具来回答用户问题。这些工具可以帮助你执行各种任务，从信息检索到代码执行再到复杂分析。
            
      ## 工具使用最佳实践

      1. **逐步思考** - 将复杂问题分解为可管理的步骤
      2. **精准调用** - 使用最合适的工具和准确的参数
      3. **结果利用** - 有效利用每个工具的结果指导后续步骤
      4. **完整回答** - 综合工具结果提供全面、准确的回答
      5. **自主判断** - 简单问题直接回答，无需调用工具

      ## 工具使用规则
      1. 必须使用正确的参数格式，使用实际值而非变量名
      2. 避免使用完全相同参数重复调用工具
      3. 如不需要工具，直接回答用户问题

      记住：你的目标是通过高效使用工具来提供最有价值的帮助。分析用户需求，选择合适工具，并以清晰、有条理的方式呈现结果。
      `
      }]


      // 构建消息历史，排除系统消息
      const chatMessages = messages
      .map(msg => ({
        role: msg.role,
        content: msg.content || '',
        ...(msg.tool_calls ? { tool_calls: msg.tool_calls } : {}),
        ...(msg.tool_call_id ? { tool_call_id: msg.tool_call_id } : {})
      }))

     
    // 构建工具定义
    const toolDefinitions = tools.map(tool => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description || '',
        parameters: tool.inputSchema || {}
      }
    }))


    // 调用通义千问API
    const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer xxxx'
      },
      body: JSON.stringify({
        model: 'qwen-plus',
        messages: chatMessages,
        temperature: 0.7,
        tools: toolDefinitions,
        parallel_tool_calls: true
      })
    })

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status} ${response.statusText}`)
    }

    const result = await response.json()
    
    // 处理返回数据
    const choice = result.choices[0]
    return {
      role: 'assistant',
      content: choice.message.content || '',
      tool_calls: choice.message.tool_calls || []
    }
  } catch (error) {
    console.error('调用通义千问API时出错:', error)
    throw error
  }
}

const call_llm_format_msg = async (message) => {
  const messages=[
        {'role': 'system', 'content': '你是一个信息整理高手,请根据输入整理成markdown格式信息'},
        {'role': 'user', 'content': message}
    ]

  // 调用通义千问API
  const response =  await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer xxx'
      },
      body: JSON.stringify({
        model: 'qwen-plus',
        messages: messages,
      })
    })

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status} ${response.statusText}`)
    }

    const result =  await response.json()
    
  // 处理返回数据
    const choice = result.choices[0]
    return {
      role: 'assistant',
      content: choice.message.content || '',
    }
}

// 发送消息处理
const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  // 添加用户消息
  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: userInput.value
  }

  // 添加系统提示
  const systemMessage: Message = {
    id: Date.now().toString() + '_system',
    role: 'system',
    content: "你是一个很有帮助的助手。如果用户提问关于天气的问题，请调用 ‘get_current_weather’ 函数;如果用户提问关于时间的问题，请调用‘get_current_time’函数。请以友好的语气回答问题。"
  }
  messages.value.push(userMessage)
  messages.value.push(systemMessage)
  loading.value = true
  
  try {
    // 构建包含系统提示的完整对话历史
    const conversationHistory = [...messages.value]
    
    // 第一次调用大模型
    let response = await callLLM(conversationHistory, availableTools.value)
    
    // 添加助手消息
    const assistantMessage: Message = {
      id: Date.now().toString() + '_assistant',
      role: 'assistant',
      content: response.content,
      tool_calls: response.tool_calls
    }
    
    messages.value.push(assistantMessage)
    
    // 处理工具调用（如果有的话）
    while (response.tool_calls && response.tool_calls.length > 0) {
      // 执行所有工具调用
      for (const toolCall of response.tool_calls) {
        try {
          const toolResult = await callTool(
            toolCall.function.name,
            JSON.parse(toolCall.function.arguments)
          )
          
          // 添加工具结果消息
          const toolMessage: Message = {
            id: `${Date.now().toString()}_tool_${toolCall.id}`,
            role: 'tool',
            content: toolResult,
            tool_call_id: toolCall.id
          }
          
          messages.value.push(toolMessage)

        // 添加最终回复
        response = await callLLM(messages.value, availableTools.value)
        const finalMessage: Message = {
          id: Date.now().toString() + '_final',
          role: 'assistant',
          content: response.content,
        }
        
          messages.value.push(finalMessage)
        
        } catch (toolError) {
          // 添加工具执行错误消息
          const toolErrorMessage: Message = {
            id: `${Date.now().toString()}_tool_error_${toolCall.id}`,
            role: 'tool',
            content: '工具执行失败: ' + (toolError as Error).message,
            tool_call_id: toolCall.id
          }
          
          messages.value.push(toolErrorMessage)
        }

      }
      
    }
  } catch (error) {
    console.error('处理消息时出错:', error)
    messages.value.push({
      id: Date.now().toString() + '_error',
      role: 'assistant',
      content: '抱歉，处理您的请求时出现错误：' + (error as Error).message
    })
  } finally {
    loading.value = false
    userInput.value = ''
  }
}
</script>

<style scoped>
.tool-agent {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 4px;
}

.message.user {
  background-color: #e3f2fd;
  margin-left: 20%;
}

.message.assistant {
  background-color: #f5f5f5;
  margin-right: 20%;
}

.message.tool {
  background-color: #e8f5e9;
  font-size: 0.9em;
}

.tool-calls {
  margin-top: 10px;
  padding: 10px;
  background-color: #fff3e0;
  border-radius: 4px;
}

.tool-call {
  font-family: monospace;
  white-space: pre-wrap;
}

.input-area {
  display: flex;
  padding: 20px;
  border-top: 1px solid #ddd;
}

.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 10px;
}

.input-area button {
  padding: 10px 20px;
  background-color: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.input-area button:disabled {
  background-color: #bbdefb;
  cursor: not-allowed;
}

.main-layout,
.sub-layout {
  height: 100%;
  border-radius: 10px;
  margin-bottom: 10px;
  background-color: #fff;
}

/* 可以选择性地引入或复制 index.vue 中的 markdown 样式 */
.markdown-wrapper {
  /* 这里可以复制 index.vue 中的样式，或者简化处理 */
  line-height: 1.6;
  width: 100%;  
}

.markdown-wrapper :deep(h1) {
  font-size: 2em;
  margin: 0.67em 0;
}

.markdown-wrapper :deep(h2) {
  font-size: 1.5em;
  margin: 0.83em 0;
}

.markdown-wrapper :deep(h3) {
  font-size: 1.17em;
  margin: 1em 0;
}

.markdown-wrapper :deep(p) {
  margin: 1em 0;
}

.markdown-wrapper :deep(ul), .markdown-wrapper :deep(ol) {
  padding-left: 2em;
  margin: 1em 0;
}

.markdown-wrapper :deep(li) {
  margin: 0.5em 0;
}

.markdown-wrapper :deep(code) {
  background-color: #f5f5f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

.markdown-wrapper :deep(pre) {
  background-color: #f5f5f5;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}

.markdown-wrapper :deep(pre > code) {
  background-color: transparent;
  padding: 0;
}

.markdown-wrapper :deep(blockquote) {
  margin: 1em 0;
  padding: 0.5em 1em;
  border-left: 4px solid #ddd;
  color: #666;
}

.markdown-wrapper :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.markdown-wrapper :deep(th), .markdown-wrapper :deep(td) {
  border: 1px solid #ddd;
  padding: 0.5em;
  text-align: left;
}

.markdown-wrapper :deep(th) {
  background-color: #f5f5f5;
}
.markdown-wrapper :deep(img) {
    width: 95%; 
    height: auto; 
    object-fit: cover; 
    display: block;
    margin: 0; 
  }
</style>