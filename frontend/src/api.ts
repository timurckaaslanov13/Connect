export type Profile = {id:number;auth_user_id:number;display_name:string;bio:string|null;avatar_url:string|null}
export type Message = {id:number;chat_id:number;sender_id:number;text:string;created_at:string;is_read:boolean}
export type Chat = {id:number;other_user_id:number;other_user_name:string|null;other_user_avatar_url:string|null;created_at:string}
export type Friend = {id:number;user_id:number;display_name:string;avatar_url:string|null;bio:string|null;status:'pending'|'accepted';direction:'incoming'|'outgoing'}
export type Summary = {chat_id:number;last_message:Message|null;unread:number}
export type CallRecord = {id:string;chat_id:number;caller_id:number;callee_id:number;media:'audio'|'video';status:string;created_at:string;answered_at:string|null;ended_at:string|null}
export class ApiError extends Error { constructor(public status:number, message:string){super(message)} }
let token = sessionStorage.getItem('connect.token') || ''
export function setToken(value:string){token=value;value?sessionStorage.setItem('connect.token',value):sessionStorage.removeItem('connect.token')}
export function getToken(){return token}
export async function api<T>(path:string, method='GET', body?:unknown):Promise<T>{
  let response:Response
  try {response=await fetch('/api'+path,{method,headers:{...(body?{'Content-Type':'application/json'}:{}),...(token?{Authorization:`Bearer ${token}`}:{})},body:body?JSON.stringify(body):undefined})}
  catch {throw new Error('Нет связи с сервером. Проверьте подключение и попробуйте ещё раз.')}
  if(response.status===204)return undefined as T
  const data=await response.json().catch(()=>({detail:'Сервер временно недоступен'}))
  if(!response.ok){
    if(response.status===401 && !['/auth/login','/auth/register'].includes(path))window.dispatchEvent(new Event('session-expired'))
    throw new ApiError(response.status,typeof data.detail==='string'?data.detail:'Проверьте заполненные поля')
  }
  return data
}
export const wsUrl=(path:string)=>`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}${path}`
export const initials=(name:string)=>(name.trim().split(/\s+/).slice(0,2).map(x=>x[0]).join('')||'C').toUpperCase()
export const clock=(date:string)=>new Date(date).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'})
export const dateLabel=(date:string)=>new Date(date).toLocaleDateString('ru-RU',{day:'numeric',month:'long'})
