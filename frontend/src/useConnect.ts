import {useCallback,useEffect,useRef,useState} from 'react'
import {api,ApiError,Chat,Profile,Friend,Message,Summary,CallRecord,getToken,setToken,wsUrl} from './api'
import {useCall,Signal} from './useCall'
export type Page='home'|'chats'|'friends'|'calls'|'profile'
type Account={id:number;email:string;username:string}
const merge=(a:Message[],b:Message[])=>[...new Map([...a,...b].map(m=>[m.id,m])).values()].sort((x,y)=>x.id-y.id)
export function useConnect(){
 const[token,changeToken]=useState(getToken()),[account,setAccount]=useState<Account|null>(null),[profile,setProfile]=useState<Profile|null>(null),[page,setPage]=useState<Page>('home'),[toast,setToast]=useState(''),[loading,setLoading]=useState(!!token),[startupError,setStartupError]=useState('')
 const[chats,setChats]=useState<Chat[]>([]),[summaries,setSummaries]=useState<Summary[]>([]),[friends,setFriends]=useState<Friend[]>([]),[records,setRecords]=useState<CallRecord[]>([]),[activeChat,setActiveChat]=useState<Chat|null>(null),[messages,setMessages]=useState<Message[]>([]),[hasOlder,setHasOlder]=useState(false),[messagesLoading,setMessagesLoading]=useState(false),[draft,setDraft]=useState(''),[sending,setSending]=useState(false),[emoji,setEmoji]=useState(false),[chatQuery,setChatQuery]=useState('')
 const[friendTab,setFriendTab]=useState<'friends'|'requests'|'search'>('friends'),[query,setQuery]=useState(''),[results,setResults]=useState<Profile[]>([]),[searching,setSearching]=useState(false),[connected,setConnected]=useState(false),[actionBusy,setActionBusy]=useState(false)
 const socket=useRef<WebSocket|null>(null),eventHandler=useRef<(data:any)=>Promise<void>>(async()=>{}),activeRef=useRef<Chat|null>(null),toastTimer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined),messageEnd=useRef<HTMLDivElement>(null),skipScroll=useRef(false),messageRequest=useRef(0)
 const notify=useCallback((s:string)=>{setToast(s);clearTimeout(toastTimer.current);toastTimer.current=setTimeout(()=>setToast(''),5500)},[])
 const sendSignal=useCallback((data:unknown)=>{if(socket.current?.readyState!==WebSocket.OPEN)throw new Error('Нет соединения. Подождите и попробуйте снова.');socket.current.send(JSON.stringify(data))},[])
 const rtc=useCall(sendSignal,notify)
 const logout=useCallback(()=>{setToken('');changeToken('');setAccount(null);setProfile(null);setChats([]);setFriends([]);setSummaries([]);setActiveChat(null);setMessages([]);setPage('home')},[])
 useEffect(()=>{const expired=()=>{rtc.clear();logout();notify('Сессия завершилась. Войдите ещё раз.')};window.addEventListener('session-expired',expired);return()=>window.removeEventListener('session-expired',expired)},[logout,notify])
 const refresh=useCallback(async()=>{const [c,f,s,r]=await Promise.all([api<Chat[]>('/chats'),api<Friend[]>('/friends'),api<Summary[]>('/messages/inbox'),api<CallRecord[]>('/calls')]);setChats(c);setFriends(f);setSummaries(s);setRecords(r)},[])
 async function initialize(){setLoading(true);setStartupError('');try{const me=await api<Account>('/auth/me');setAccount(me);let p:Profile;try{p=await api<Profile>('/users/profile')}catch(error){if(error instanceof ApiError&&error.status===404)p=await api<Profile>('/users/profile','POST',{display_name:me.username});else throw error}setProfile(p);await refresh()}catch(error){setStartupError((error as Error).message)}finally{setLoading(false)}}
 useEffect(()=>{if(token)void initialize()},[token])
 useEffect(()=>{
  if(!token)return
  let busy=false
  const sync=async()=>{if(busy||document.visibilityState==='hidden')return;busy=true;try{await refresh();const chat=activeRef.current;if(chat)await loadMessages(chat,false)}catch{/* Retry on the next tick or focus. */}finally{busy=false}}
  const interval=setInterval(()=>void sync(),5000)
  const wake=()=>void sync()
  window.addEventListener('online',wake);window.addEventListener('focus',wake);document.addEventListener('visibilitychange',wake)
  return()=>{clearInterval(interval);window.removeEventListener('online',wake);window.removeEventListener('focus',wake);document.removeEventListener('visibilitychange',wake)}
 },[token,refresh])
 useEffect(()=>{activeRef.current=activeChat},[activeChat])
 useEffect(()=>{if(skipScroll.current){skipScroll.current=false;return}messageEnd.current?.scrollIntoView({behavior:'smooth',block:'end'})},[messages.length])
 useEffect(()=>{if(!token)return;let cancelled=false,timer:ReturnType<typeof setTimeout>,heartbeat:ReturnType<typeof setInterval>,attempt=0;let queue=Promise.resolve();const connect=()=>{
  if(cancelled)return;const ws=new WebSocket(wsUrl('/ws/events'));socket.current=ws
  ws.onopen=()=>{ws.send(JSON.stringify({type:'auth',token}));heartbeat=setInterval(()=>{if(ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:'ping'}))},20000)}
  ws.onmessage=e=>{try{const event=JSON.parse(e.data);if(event.type==='ready'){setConnected(true);attempt=0;void refresh().catch(()=>{});const current=activeRef.current;if(current)void loadMessages(current,false);return}queue=queue.then(()=>eventHandler.current(event)).catch(()=>notify('Не удалось обновить событие.'))}catch{/* invalid server frame */}}
  ws.onclose=e=>{clearInterval(heartbeat);setConnected(false);if(cancelled)return;if(e.code===1008){window.dispatchEvent(new Event('session-expired'));return}rtc.clear();timer=setTimeout(connect,Math.min(1000*2**attempt++,15000))};ws.onerror=()=>ws.close()
 };connect();return()=>{cancelled=true;clearTimeout(timer);clearInterval(heartbeat);socket.current?.close();socket.current=null;setConnected(false)}},[token])
 eventHandler.current=async event=>{
  if(event.type==='message'){const m:Message=event.message;if(activeRef.current?.id===m.chat_id){setMessages(old=>merge(old,[m]));if(m.sender_id!==account?.id)void api(`/messages/chat/${m.chat_id}/read`,'POST').catch(()=>{})}setSummaries(old=>{const found=old.find(s=>s.chat_id===m.chat_id),updated={chat_id:m.chat_id,last_message:m,unread:activeRef.current?.id===m.chat_id||m.sender_id===account?.id?0:(found?.unread||0)+1};return [...old.filter(s=>s.chat_id!==m.chat_id),updated]});if(!chats.some(c=>c.id===m.chat_id))void refresh().catch(()=>{});return}
  if(event.type==='read'){if(event.user_id!==account?.id)setMessages(old=>old.map(m=>m.chat_id===event.chat_id&&m.sender_id===account?.id&&m.id<=event.last_id?{...m,is_read:true}:m));else setSummaries(old=>old.map(s=>s.chat_id===event.chat_id?{...s,unread:0}:s));return}
  if(event.type?.startsWith('call.')){let name=chats.find(c=>c.other_user_id===event.sender_id)?.other_user_name||friends.find(f=>f.user_id===event.sender_id)?.display_name||undefined;if(event.type==='call.invite'&&!name){try{name=(await api<Profile>(`/users/by-auth-id/${event.sender_id}`)).display_name}catch{}}await rtc.receive(event as Signal,name);if(event.type==='call.end')void refresh().catch(()=>{})}
 }
 async function loadMessages(chat:Chat,reset=true,before?:number){const request=++messageRequest.current;setMessagesLoading(true);try{const rows=await api<Message[]>(`/messages/chat/${chat.id}?latest=true&limit=50${before?'&before_id='+before:''}`);if(request!==messageRequest.current)return;if(before)skipScroll.current=true;setMessages(old=>merge(old,rows));if(reset||before)setHasOlder(rows.length===50);await api(`/messages/chat/${chat.id}/read`,'POST');setSummaries(old=>old.map(s=>s.chat_id===chat.id?{...s,unread:0}:s))}catch(e){notify((e as Error).message)}finally{if(request===messageRequest.current)setMessagesLoading(false)}}
 function openChat(chat:Chat){setPage('chats');setActiveChat(chat);activeRef.current=chat;setMessages([]);setDraft('');setEmoji(false);void loadMessages(chat)}
 function closeChat(){setActiveChat(null);activeRef.current=null;messageRequest.current++}
 async function startChat(userId:number,name:string){setActionBusy(true);try{const row=await api<{id:number;created_at:string}>('/chats/private','POST',{other_user_id:userId});const chat={id:row.id,other_user_id:userId,other_user_name:name,other_user_avatar_url:null,created_at:row.created_at};await refresh();openChat(chat)}catch(e){notify((e as Error).message)}finally{setActionBusy(false)}}
 async function sendMessage(e:React.FormEvent){e.preventDefault();if(!activeChat||!draft.trim()||sending)return;setSending(true);const text=draft,chatId=activeChat.id;try{const m=await api<Message>('/messages','POST',{chat_id:chatId,text});if(activeRef.current?.id===chatId){setMessages(old=>merge(old,[m]));setDraft('')}void refresh().catch(()=>{})}catch(e){notify((e as Error).message)}finally{setSending(false)}}
 function go(destination:Page){setPage(destination);if(destination!=='chats')closeChat()}
 function findPeople(){go('friends');setFriendTab('search')}
 useEffect(()=>{if(!token||query.trim().length<2){setResults([]);setSearching(false);return}let cancelled=false;setSearching(true);const timer=setTimeout(()=>{api<Profile[]>(`/users/search?q=${encodeURIComponent(query.trim())}`).then(rows=>{if(!cancelled)setResults(rows.filter(r=>r.auth_user_id!==account?.id))}).catch(e=>{if(!cancelled)notify(e.message)}).finally(()=>{if(!cancelled)setSearching(false)})},300);return()=>{cancelled=true;clearTimeout(timer)}},[query,token,account?.id])
 async function friendAction(path:string,method='POST',body?:unknown){setActionBusy(true);try{await api(path,method,body);await refresh();notify(method==='DELETE'?'Готово':path.endsWith('/accept')?'Теперь вы друзья':'Заявка отправлена')}catch(e){notify((e as Error).message)}finally{setActionBusy(false)}}
 async function saveProfile(e:React.FormEvent<HTMLFormElement>){e.preventDefault();setActionBusy(true);const form=new FormData(e.currentTarget);try{setProfile(await api<Profile>('/users/profile','PATCH',{display_name:form.get('name'),bio:form.get('bio')}));notify('Профиль обновлён')}catch(e){notify((e as Error).message)}finally{setActionBusy(false)}}
 const accepted=friends.filter(f=>f.status==='accepted'),incoming=friends.filter(f=>f.status==='pending'&&f.direction==='incoming'),unread=summaries.reduce((n,s)=>n+s.unread,0),name=profile?.display_name||account?.username||'Друг'
 const summary=(chatId:number)=>summaries.find(s=>s.chat_id===chatId)
 const sortedChats=[...chats].sort((a,b)=>(summary(b.id)?.last_message?.id||0)-(summary(a.id)?.last_message?.id||0))
 const personName=(id:number)=>chats.find(c=>c.other_user_id===id)?.other_user_name||friends.find(f=>f.user_id===id)?.display_name||`Пользователь ${id}`
 return {token,changeToken,account,profile,page,toast,setToast,loading,startupError,initialize,notify,logout,rtc,refresh,chats,sortedChats,summary,unread,friends,accepted,incoming,name,records,activeChat,openChat,closeChat,startChat,messages,hasOlder,messagesLoading,loadMessages,messageEnd,draft,setDraft,sending,sendMessage,emoji,setEmoji,chatQuery,setChatQuery,go,findPeople,friendTab,setFriendTab,query,setQuery,results,searching,connected,actionBusy,friendAction,personName,saveProfile}
}
export type Connect=ReturnType<typeof useConnect>
