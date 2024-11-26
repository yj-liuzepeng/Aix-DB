<script lang="tsx" setup>
import { isMockDevelopment ***REMOVED*** from '@/config'
import { type InputInst ***REMOVED*** from 'naive-ui'
import { useRouter ***REMOVED*** from 'vue-router'
import { UAParser ***REMOVED*** from 'ua-parser-js'
import TableModal from './TableModal.vue'
import DefaultPage from './DefaultPage.vue'
const route = useRoute(***REMOVED***
const router = useRouter(***REMOVED***
const message = useMessage(***REMOVED***

// 显示默认页面
const showDefaultPage = ref(true***REMOVED***

//全局存储
const businessStore = useBusinessStore(***REMOVED***

//是否是刚登录到系统 批量渲染对话记录
const isInit = ref(false***REMOVED***

// 使用 onMounted 生命周期钩子加载历史对话
onMounted((***REMOVED*** => {
    fetchConversationHistory(
        isInit,
        conversationItems,
        tableData,
        currentRenderIndex
    ***REMOVED***
***REMOVED******REMOVED***

//管理对话
const isModalOpen = ref(false***REMOVED***
function openModal(***REMOVED*** {
    isModalOpen.value = true
***REMOVED***
//模态框关闭
function handleModalClose(value***REMOVED*** {
    isModalOpen.value = value
    //重新加载对话记录
    fetchConversationHistory(
        isInit,
        conversationItems,
        tableData,
        currentRenderIndex
    ***REMOVED***
***REMOVED***

//新建对话
function newChat(***REMOVED*** {
    showDefaultPage.value = true
    isInit.value = false
    conversationItems.value = []
***REMOVED***

/**
 * 默认大模型
 */
const defaultLLMTypeName = 'qwen2'
const currentChatId = computed((***REMOVED*** => {
    return route.params.chatId
***REMOVED******REMOVED***

//主页面加载提示
const loading = ref(true***REMOVED***
setTimeout((***REMOVED*** => {
***REMOVED***
***REMOVED******REMOVED***

//对话等待提示词图标
const stylizingLoading = ref(false***REMOVED***

//输入字符串
const inputTextString = ref(''***REMOVED***
const refInputTextString = ref<InputInst | null>(***REMOVED***

//输出字符串 Reader 流（风格化的）
const outputTextReader = ref<ReadableStreamDefaultReader | null>(***REMOVED***

//markdown对象
const refReaderMarkdownPreview = ref<any>(***REMOVED***

//主内容区域
const messagesContainer = ref<HTMLElement | null>(null***REMOVED***

//读取失败
const onFailedReader = (index: number***REMOVED*** => {
    if (conversationItems.value[index]***REMOVED*** {
        conversationItems.value[index].reader = null
        stylizingLoading.value = false
        if (refReaderMarkdownPreview.value***REMOVED*** {
            refReaderMarkdownPreview.value.initializeEnd(***REMOVED***
        ***REMOVED***
        window.$ModalMessage.error('请求失败，请重试'***REMOVED***
        setTimeout((***REMOVED*** => {
            if (refInputTextString.value***REMOVED*** {
                refInputTextString.value.focus(***REMOVED***
            ***REMOVED***
        ***REMOVED******REMOVED***
    ***REMOVED***
***REMOVED***

//读取完成
const onCompletedReader = (index: number***REMOVED*** => {
    if (conversationItems.value[index]***REMOVED*** {
        stylizingLoading.value = false
        setTimeout((***REMOVED*** => {
            if (refInputTextString.value***REMOVED*** {
                refInputTextString.value.focus(***REMOVED***
            ***REMOVED***
        ***REMOVED******REMOVED***
    ***REMOVED***
    // scrollToBottom(***REMOVED***
***REMOVED***

//图表子组件渲染完毕
const currentRenderIndex = ref(0***REMOVED***
const onChartReady = (index***REMOVED*** => {
    if (index < conversationItems.value.length***REMOVED*** {
        currentRenderIndex.value = index
        stylizingLoading.value = false
    ***REMOVED***
***REMOVED***

// 侧边栏对话历史
interface TableItem {
    index: number
    key: string
***REMOVED***
const tableData = ref<TableItem[]>([]***REMOVED***

//保存对话历史记录
const conversationItems = ref<
    Array<{
        role: 'user' | 'assistant'
        reader: ReadableStreamDefaultReader | null
    ***REMOVED***>
>([]***REMOVED***

// 这里子组件 chart渲染慢需要子组件渲染完毕后通知父组件
const visibleConversationItems = computed((***REMOVED*** => {
    return conversationItems.value.slice(0, currentRenderIndex.value + 1***REMOVED***
***REMOVED******REMOVED***

//提交对话
const handleCreateStylized = async (send_text = ''***REMOVED*** => {
    // isInit.value = false
    // 若正在加载，则点击后恢复初始状态
    if (stylizingLoading.value***REMOVED*** {
        onCompletedReader(conversationItems.value.length - 1***REMOVED***
        return
    ***REMOVED***

    //send_text 为空代表数据问答
    if (send_text == ''***REMOVED*** {
        if (refInputTextString.value && !inputTextString.value.trim(***REMOVED******REMOVED*** {
            inputTextString.value = ''
            refInputTextString.value.focus(***REMOVED***
            return
        ***REMOVED***
    ***REMOVED***

    // 新建对话 时输入新问题 清空历史数据
    if (showDefaultPage.value***REMOVED*** {
        conversationItems.value = []
        showDefaultPage.value = false
        isInit.value = false
    ***REMOVED***

    //加入对话历史用于左边表格渲染
    tableData.value.push({
        index: tableData.value.length,
        key: inputTextString.value
    ***REMOVED******REMOVED***

    //调用大模型后台服务接口
    stylizingLoading.value = true
    const textContent = inputTextString.value
        ? inputTextString.value
        : send_text
    inputTextString.value = ''
    const { error, reader, needLogin ***REMOVED*** =
        await businessStore.createAssistantWriterStylized(currentChatId.value, {
            text: textContent,
            writer_oid: currentChatId.value
        ***REMOVED******REMOVED***

    if (needLogin***REMOVED*** {
        message.error('登录已失效，请重新登录'***REMOVED***

        //跳转至登录页面
        setTimeout((***REMOVED*** => {
            router.push('/login'***REMOVED***
        ***REMOVED***, 2000***REMOVED***
    ***REMOVED***

    if (error***REMOVED*** {
        stylizingLoading.value = false
        onCompletedReader(conversationItems.value.length - 1***REMOVED***
        return
    ***REMOVED***

    if (reader***REMOVED*** {
        outputTextReader.value = reader
        // 添加助手的回答
        conversationItems.value.push({
      ***REMOVED***
            reader: reader
        ***REMOVED******REMOVED***
        // 更新 currentRenderIndex 以包含新添加的项
        currentRenderIndex.value = conversationItems.value.length - 1
    ***REMOVED***

    // 滚动到底部
    scrollToBottom(***REMOVED***
***REMOVED***

// 滚动到底部
const scrollToBottom = (***REMOVED*** => {
    nextTick((***REMOVED*** => {
        if (messagesContainer.value***REMOVED*** {
            messagesContainer.value.scrollTop =
                messagesContainer.value.scrollHeight
        ***REMOVED***
    ***REMOVED******REMOVED***
***REMOVED***

const keys = useMagicKeys(***REMOVED***
const enterCommand = keys['Enter']
const enterCtrl = keys['Enter']

const activeElement = useActiveElement(***REMOVED***
const notUsingInput = computed(
    (***REMOVED*** => activeElement.value?.tagName !== 'TEXTAREA'
***REMOVED***

const parser = new UAParser(***REMOVED***
const isMacos = parser.getOS(***REMOVED***.name.includes('Mac'***REMOVED***

const placeholder = computed((***REMOVED*** => {
    if (stylizingLoading.value***REMOVED*** {
        return `输入任意问题...`
    ***REMOVED***
    return `输入任意问题, 按 ${
        isMacos ? 'Command' : 'Ctrl'
    ***REMOVED*** + Enter 键快捷开始...`
***REMOVED******REMOVED***

const generateRandomSuffix = function (***REMOVED*** {
    return Math.floor(Math.random(***REMOVED*** * 10000***REMOVED*** // 生成0到9999之间的随机整数
***REMOVED***

watch(
    (***REMOVED*** => enterCommand.value,
    (***REMOVED*** => {
        if (!isMacos || notUsingInput.value***REMOVED*** return

        if (stylizingLoading.value***REMOVED*** return

        if (!enterCommand.value***REMOVED*** {
            handleCreateStylized(***REMOVED***
        ***REMOVED***
    ***REMOVED***,
  ***REMOVED***
        deep: true
    ***REMOVED***
***REMOVED***

watch(
    (***REMOVED*** => enterCtrl.value,
    (***REMOVED*** => {
        if (isMacos || notUsingInput.value***REMOVED*** return

        if (stylizingLoading.value***REMOVED*** return

        if (!enterCtrl.value***REMOVED*** {
            handleCreateStylized(***REMOVED***
        ***REMOVED***
    ***REMOVED***,
  ***REMOVED***
        deep: true
    ***REMOVED***
***REMOVED***

const handleResetState = (***REMOVED*** => {
    if (isMockDevelopment***REMOVED*** {
        inputTextString.value = ''
    ***REMOVED*** else {
        inputTextString.value = ''
    ***REMOVED***

    stylizingLoading.value = false
    nextTick((***REMOVED*** => {
        refInputTextString.value?.focus(***REMOVED***
    ***REMOVED******REMOVED***
    refReaderMarkdownPreview.value?.abortReader(***REMOVED***
    refReaderMarkdownPreview.value?.resetStatus(***REMOVED***
***REMOVED***
handleResetState(***REMOVED***

//文件上传
let file_name = ref(''***REMOVED***
const finish_upload = (res***REMOVED*** => {
    file_name.value = res.file.name
    if (res.event.target.responseText***REMOVED*** {
        let json_data = JSON.parse(res.event.target.responseText***REMOVED***
        let file_url = json_data['data']['object_key']
        if (json_data['code'] == 200***REMOVED*** {
            //  businessStore.update_qa_type('FILEDATA_QA'***REMOVED***
            businessStore.update_file_url(file_url***REMOVED***
            window.$ModalMessage.success(`文件上传成功`***REMOVED***
        ***REMOVED*** else {
            window.$ModalMessage.error(`文件上传失败`***REMOVED***
        ***REMOVED***
        handleCreateStylized(file_name.value + ' 总结归纳文档的关键信息'***REMOVED***
    ***REMOVED***
***REMOVED***

// 下面方法用于左侧对话列表点击 右侧内容滚动
// 用于存储每个 MarkdownPreview 容器的引用
const markdownPreviews = ref<Array<HTMLElement | null>>([]***REMOVED*** // 初始化为空数组

// 表格行点击事件
const rowProps = (row: any***REMOVED*** => {
***REMOVED***
        onClick: (***REMOVED*** => {
            scrollToItem(row.index***REMOVED***
        ***REMOVED***
    ***REMOVED***
***REMOVED***

// 设置 markdownPreviews 数组中的元素
const setMarkdownPreview = (index: number, el: any***REMOVED*** => {
    if (el && el instanceof HTMLElement***REMOVED*** {
        // 确保 markdownPreviews 数组的长度与 visibleConversationItems 的长度一致
        if (index >= markdownPreviews.value.length***REMOVED*** {
            markdownPreviews.value.push(null***REMOVED***
        ***REMOVED***
        markdownPreviews.value[index] = el
    ***REMOVED*** else if (el && el.value && el.value instanceof HTMLElement***REMOVED*** {
        // 处理代理对象的情况
        if (index >= markdownPreviews.value.length***REMOVED*** {
            markdownPreviews.value.push(null***REMOVED***
        ***REMOVED***
        markdownPreviews.value[index] = el.value
    ***REMOVED***
***REMOVED***

// 滚动到指定位置的方法
const scrollToItem = (index: number***REMOVED*** => {
    //判断默认页面是否显示或对话历史是否初始化
    if (
        (!showDefaultPage.value && !isInit.value***REMOVED*** ||
        conversationItems.value.length === 0
    ***REMOVED*** {
        fetchConversationHistory(
            isInit,
            conversationItems,
            tableData,
            currentRenderIndex
        ***REMOVED***
        console.log(isInit.value***REMOVED***
    ***REMOVED***
    //关闭默认页面
    showDefaultPage.value = false
    if (markdownPreviews.value[index]***REMOVED*** {
        markdownPreviews.value[index].scrollIntoView({ behavior: 'smooth' ***REMOVED******REMOVED***
    ***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
    <LayoutCenterPanel :loading="loading">
        <template #sidebar-header>
            <n-button
                type="primary"
                icon-placement="left"
                color="#5e58e7"
                @click="newChat"
                strong
                style="
                    width: 160px;
                    height: 38px;
                    margin: 15px;
                    align-self: center;
                    text-align: center;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                        Roboto, 'Helvetica Neue', Arial, sans-serif;
                    font-weight: bold;
                    font-size: 14px;
                "
  ***REMOVED***
                <template #icon>
                    <n-icon style="margin-right: 5px">
              ***REMOVED***class="i-hugeicons:add-01"></div>
                    </n-icon>
                ***REMOVED***
                新建对话
            </n-button>
        ***REMOVED***

        <template #sidebar>
            <n-data-table
                class="custom-table"
                style="
                    --n-td-color-hover: #d5dcff;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                        Roboto, 'Helvetica Neue', Arial, sans-serif;
                "
                size="small"
                :bordered="false"
                :bottom-bordered="false"
                :columns="[
                  ***REMOVED*** key: 'key', align: 'left', ellipsis: { tooltip: false ***REMOVED*** ***REMOVED***
            ***REMOVED***"
                :data="tableData"
                :row-props="rowProps"
  ***REMOVED***
                <template #empty>
                    <div></div>
                ***REMOVED***
            </n-data-table>
        ***REMOVED***

        <template #sidebar-action>
            <n-divider style="width: 180px" />
            <n-button
                quaternary
                icon-placement="left"
                type="primary"
                strong
                @click="openModal"
                style="
                    width: 150px;
                    height: 38px;
                    align-self: center;
                    text-align: center;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                        Roboto, 'Helvetica Neue', Arial, sans-serif;
                    font-size: 14px;
                "
  ***REMOVED***
                <template #icon>
                    <n-icon>
              ***REMOVED***class="i-hugeicons:voice-id"></div>
                    </n-icon>
                ***REMOVED***
                管理对话
            </n-button>

            <TableModal :show="isModalOpen" @update:show="handleModalClose" />
        ***REMOVED***
        <!-- 内容区域 -->
        <div flex="~ col" h-full style="background-color: #f6f7fb">
  ***REMOVED***flex="~ justify-between items-center">
                <NavigationNavBar />
***REMOVED***

            <!--这里循环渲染即可实现多轮对话-->
            <div
                flex="1 ~ col"
                min-h-0
                pb-20
                class="scrollable-container"
                ref="messagesContainer"
  ***REMOVED***
      ***REMOVED***v-if="showDefaultPage">
                    <DefaultPage />
    ***REMOVED***

                <div
                    v-if="!showDefaultPage"
                    v-for="(item, index***REMOVED*** in visibleConversationItems"
                    :key="index"
                    class="mb-4"
                    :ref="(el***REMOVED*** => setMarkdownPreview(index, el***REMOVED***"
      ***REMOVED***
                    <MarkdownPreview
                        :reader="item.reader"
                        :model="defaultLLMTypeName"
                        :isInit="isInit"
                        :chart-id="`${index***REMOVED***devID${generateRandomSuffix(***REMOVED******REMOVED***`"
                        :parentScollBottomMethod="scrollToBottom"
                        @failed="(***REMOVED*** => onFailedReader(index***REMOVED***"
                        @completed="(***REMOVED*** => onCompletedReader(index***REMOVED***"
                        @chartready="(***REMOVED*** => onChartReady(index + 1***REMOVED***"
          ***REMOVED***
    ***REMOVED***
***REMOVED***

            <div
                style="display: flex; align-items: center"
                flex-basis="10%"
                p="14px"
                py="0"
  ***REMOVED***
                <div>
                    <n-upload
                        type="button"
                        :show-file-list="false"
                        action="sanic/file/upload_file"
                        accept=".xlsx,.xls,.csv"
                        class="mr-2"
                        v-on:finish="finish_upload"
          ***REMOVED***
                        <n-icon size="35"
                  ***REMOVED***<svg
                                t="1729566080604"
                                class="icon"
                                viewBox="0 0 1024 1024"
                                version="1.1"
                                xmlns="http://www.w3.org/2000/svg"
                                p-id="38910"
                                width="64"
                                height="64"
                  ***REMOVED***
                                <path
                                    d="M856.448 606.72v191.744a31.552 31.552 0 0 1-31.488 31.488H194.624a31.552 31.552 0 0 1-31.488-31.488V606.72a31.488 31.488 0 1 1 62.976 0v160.256h567.36V606.72a31.488 31.488 0 1 1 62.976 0zM359.872 381.248c-8.192 0-10.56-5.184-5.376-11.392L500.48 193.152a11.776 11.776 0 0 1 18.752 0l145.856 176.704c5.184 6.272 2.752 11.392-5.376 11.392H359.872z"
                                    fill="#838384"
                                    p-id="38911"
                      ***REMOVED***</path>
                                <path
                                    d="M540.288 637.248a30.464 30.464 0 1 1-61.056 0V342.656a30.464 30.464 0 1 1 61.056 0v294.592z"
                                    fill="#838384"
                                    p-id="38912"
                      ***REMOVED***</path>
                            </svg>
                        </n-icon>
                    </n-upload>
    ***REMOVED***
                <div
                    style="
                        position: relative;
                      ***REMOVED***
                      ***REMOVED***
                      ***REMOVED***
                    "
      ***REMOVED***
                    <n-space vertical>
                        <n-input
                            ref="refInputTextString"
                            v-model:value="inputTextString"
                            type="textarea"
                            autofocus
                            h-full
                            class="textarea-resize-none text-15"
                            :style="{
                                '--n-border-radius': '100px',
                                '--n-padding-left': '20px',
                                '--n-padding-right': '20px',
                                '--n-padding-vertical': '15px'
                            ***REMOVED***"
                            :placeholder="placeholder"
                            :autosize="{
                                minRows: 1,
                                maxRows: 5
                            ***REMOVED***"
              ***REMOVED***
                        <n-float-button
                            position="absolute"
                            :right="25"
                            top="45%"
                            :type="stylizingLoading ? 'primary' : 'default'"
                            color
                            :class="[
                                stylizingLoading && 'opacity-90',
                                'text-20'
                        ***REMOVED***"
                            style="transform: translateY(-50%***REMOVED***"
                            @click.stop="handleCreateStylized(***REMOVED***"
              ***REMOVED***
                            <div
                                v-if="stylizingLoading"
                                class="i-svg-spinners:pulse-2 c-#fff"
                  ***REMOVED***</div>
                            <div
                                v-else
                                class="flex items-center justify-center c-#303133/60 i-mingcute:send-fill"
                  ***REMOVED***</div>
                        </n-float-button>
                    </n-space>
    ***REMOVED***
***REMOVED***
***REMOVED***
    </LayoutCenterPanel>
***REMOVED***

<style lang="scss" scoped>
.scrollable-container {
  ***REMOVED*** // 添加纵向滚动条
    max-height: calc(
        100vh - 120px
    ***REMOVED***; // 设置最大高度，确保输入框和导航栏有足够的空间
    padding-bottom: 20px; // 底部内边距，防止内容被遮挡
    background-color: #f6f7fb;
***REMOVED***
/* 滚动条整体部分 */
::-webkit-scrollbar {
    width: 4px; /* 竖向滚动条宽度 */
    height: 4px; /* 横向滚动条高度 */
***REMOVED***

/* 滚动条的轨道 */
::-webkit-scrollbar-track {
    background: #fff; /* 轨道背景色 */
***REMOVED***

/* 滚动条的滑块 */
::-webkit-scrollbar-thumb {
    background: #cac9f9; /* 滑块颜色 */
  ***REMOVED*** /* 滑块圆角 */
***REMOVED***

/* 滚动条的滑块在悬停状态下的样式 */
::-webkit-scrollbar-thumb:hover {
    background: #cac9f9; /* 悬停时滑块颜色 */
***REMOVED***

:deep(.custom-table .n-data-table-thead***REMOVED*** {
    display: none;
***REMOVED***
.default-page {
  ***REMOVED***
    justify-content: center;
    align-items: center;
    height: 100vh; /* 使容器高度占满整个视口 */
    background-color: #f0f2f5; /* 可选：设置背景颜色 */
***REMOVED***
***REMOVED***
