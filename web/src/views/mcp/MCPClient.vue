<script lang="tsx" setup>
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js'

const message = ref('')
const messages = ref('')
const connectionStatus = ref('Disconnected')
// https://github.com/modelcontextprotocol/typescript-sdk
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

onMounted(async () => {
  await client.connect(transport)
  connectionStatus.value = 'Connected'
  const tools = await client.listTools()
  console.log(tools)
})

const sendMessage = async () => {
  const result = await client.callTool({
    name: 'amap-maps_weather',
    arguments: {
      city: message.value,
    },
  })
  messages.value = JSON.stringify(result.content)
  console.log(result.content)
}




// List prompts
// const prompts = await client.listPrompts()
// console.log(prompts)

// // Get a prompt
// const prompt = await client.getPrompt('example-prompt', {
//     arg1: 'value'
// })

// List resources
// const resources = await client.listResources()

// // Read a resource
// const resource = await client.readResource('file:///example.txt')
</script>

<template>
  <n-layout class="main-layout" style="height: 100vh">
    <div class="mcp-client">
      <h1>MCP Client</h1>
      <p>Connection Status: {{ connectionStatus }}</p>

      <!-- 输入框和按钮 -->
      <div>
        <input
          v-model="message"
          style="width: 280px; height: 25px"
          placeholder="Enter message to send"
        >
        <button
          style="height: 25px; margin-left: 2px; width: 80px"
          @click="sendMessage"
        >
          Send
        </button>
      </div>

      <!-- 消息日志 -->
      <div class="message-log">
        <h3>Message Log:</h3>
        <ul>
          {{
            messages
          }}
        </ul>
      </div>
    </div>
  </n-layout>
</template>

<style scoped>
/* 全局样式 */

.note-box {
  max-width: 600px;
  margin: 20px auto 0;
  background: #f8f9fa;
  border-left: 4px solid #3b82f6;
  border-radius: 4px;
  padding: 15px;
}

.note-box ul {
  margin: 10px 0 0 20px;
}

.note-box li {
  list-style-type: disc;
  margin: 5px 0;
}

/* 保持原有 scoped 样式 */

.mcp-client {
  font-family: Arial, sans-serif;
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  margin-top: 20px;
}

.message-log {
  margin-top: 20px;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  background: #f9f9f9;
  margin: 5px 0;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.main-layout,
.sub-layout {
  height: 100%;
  border-radius: 10px;
  margin-bottom: 10px;
  background-color: #fff;
}
</style>
