<script lang="ts" setup>
interface Props {
  loading?: boolean
***REMOVED***
withDefaults(defineProps<Props>(***REMOVED***, {
  loading: false,
***REMOVED******REMOVED***

const userStore = useUserStore(***REMOVED***
const router = useRouter(***REMOVED***
const logout = (***REMOVED*** => {
  userStore.logout(***REMOVED***
  setTimeout((***REMOVED*** => {
    router.push('/login'***REMOVED***
  ***REMOVED***, 500***REMOVED***
***REMOVED***
const handleClickEfficiency = (index***REMOVED*** => {
  router.push('/testAssitant'***REMOVED***
***REMOVED***

const handleClickChat = (index***REMOVED*** => {
  router.push('/chat'***REMOVED***
***REMOVED***

const handleClick = (***REMOVED*** => {
  router.push('/mcpChat'***REMOVED***
***REMOVED***

// 使用ref定义响应式的selectedIndex
const selectedIndex = ref(0***REMOVED***
onMounted((***REMOVED*** => {
  // 初始化selectedIndex为0
  router.currentRoute.value.path === '/testAssitant'
    ? (selectedIndex.value = 2***REMOVED***
    : (selectedIndex.value = 1***REMOVED***
***REMOVED******REMOVED***
***REMOVED***

***REMOVED***
  <LayoutSlotFrame :class="['bg-no-repeat bg-cover bg-center']">
    <template #center>
      <div
        flex="~"
        size-full
        overflow-hidden
        class="panel-shadow"
      >
        <n-spin
          w-full
          h-full
          content-class="w-full h-full flex"
          :show="false"
          :rotate="false"
          class="bg-#ffffff"
          :style="{
            '--n-opacity-spinning': '0',
          ***REMOVED***"
        >
          <section
            flex="~ col"
            min-w-0
            w-70
            h-full
            overflow-hidden
            relative
***REMOVED***
            <NavigationSideBar />
          </section>
          <section
            flex="1 ~"
            min-w-0
            h-full
            overflow-hidden
            py-12
            pr-12
            style="background: linear-gradient(to bottom, #8874f1, #588af9***REMOVED***"
***REMOVED***
            <div
              size-full
              rounded-10
              overflow-hidden
  ***REMOVED***
              <LayoutDefault />
***REMOVED***
          </section>
        </n-spin>
***REMOVED***
    ***REMOVED***
    <template #bottom>
      <NavigationNavFooter />
    ***REMOVED***
  </LayoutSlotFrame>
***REMOVED***

<style lang="scss" scoped>
.panel-shadow {
  --shadow: 50px 50px 100px 10px rgb(0 0 0 / 10%***REMOVED***;
  --at-apply: 'shadow-[--shadow]';
***REMOVED***
***REMOVED***
