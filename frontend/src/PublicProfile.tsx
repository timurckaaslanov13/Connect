import {useEffect,useRef,useState} from 'react'
import {Check,Heart,LoaderCircle,MessageCircle,UserPlus,X} from 'lucide-react'
import {api,Profile} from './api'
import {Avatar} from './components'
import {Connect} from './useConnect'

export function PublicProfile({app:a}:{app:Connect}){
 const dialog=useRef<HTMLDialogElement>(null)
 const[profile,setProfile]=useState<Profile|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0)
 const id=a.viewedUser
 useEffect(()=>{
  if(id===null){dialog.current?.close();return}
  dialog.current?.showModal()
  let cancelled=false
  setProfile(null);setError('')
  Promise.all([api<Profile>(`/users/by-auth-id/${id}`),api<{username:string}>(`/auth/directory/${id}`)])
   .then(([p,account])=>{if(!cancelled)setProfile({...p,username:account.username})})
   .catch(e=>{if(!cancelled)setError(e.message)})
  return()=>{cancelled=true}
 },[id,retry])
 useEffect(()=>{if(a.rtc.call)a.openProfile(null)},[a.rtc.call?.id])
 const relation=a.friends.find(f=>f.user_id===id)
 const close=()=>a.openProfile(null)
 async function write(){if(!profile)return;if(a.page==='chats'&&a.activeChat?.other_user_id===profile.auth_user_id){close();return}await a.startChat(profile.auth_user_id,profile.display_name);close()}
 return <dialog ref={dialog} className="public-profile-dialog" aria-labelledby="public-profile-title" onCancel={close} onClose={close} onClick={e=>{if(e.target===dialog.current)close()}}>
  <section className="public-profile-content">
   <div className="profile-cover"><span>Больше, чем общение.</span><Heart size={36}/><button autoFocus className="icon-button public-profile-close" aria-label="Закрыть профиль" onClick={close}><X/></button></div>
   <h2 id="public-profile-title" className="sr-only">Профиль пользователя</h2>
   {error?<div className="empty"><h3>Не удалось открыть профиль</h3><p role="alert">{error}</p><button className="secondary" onClick={()=>setRetry(x=>x+1)}>Попробовать снова</button></div>:!profile?<div className="empty" role="status"><LoaderCircle className="spin"/><p>Загружаем профиль…</p></div>:<div className="public-profile-body">
    <Avatar name={profile.display_name} id={profile.auth_user_id} url={profile.avatar_url} size="extra-large"/>
    <h2>{profile.display_name}</h2><p className="public-nickname">@{profile.username}</p>
    <div className="public-bio"><h3>О себе</h3><p>{profile.bio||'Пользователь пока ничего о себе не рассказал.'}</p></div>
    {id===a.account?.id?<button className="primary" onClick={()=>{close();a.go('profile')}}>Редактировать свой профиль</button>:<div className="public-profile-actions">
     <button className="primary" disabled={a.actionBusy} onClick={()=>void write()}><MessageCircle size={18}/> Написать сообщение</button>
     {!relation?<button className="secondary" disabled={a.actionBusy} onClick={()=>void a.friendAction('/friends/requests','POST',{user_id:id})}><UserPlus size={18}/> Добавить в друзья</button>:relation.status==='accepted'?<><span className="relationship"><Check size={17}/> У вас в друзьях</span><button className="subtle-button" disabled={a.actionBusy} onClick={()=>{if(confirm(`Убрать ${profile.display_name} из друзей?`))void a.friendAction(`/friends/${relation.id}`,'DELETE')}}>Убрать из друзей</button></>:relation.direction==='incoming'?<><button className="secondary" disabled={a.actionBusy} onClick={()=>void a.friendAction(`/friends/requests/${relation.id}/accept`)}>Принять заявку</button><button className="subtle-button" disabled={a.actionBusy} onClick={()=>void a.friendAction(`/friends/${relation.id}`,'DELETE')}>Отклонить заявку</button></>:<><span className="relationship"><Check size={17}/> Заявка отправлена</span><button className="subtle-button" disabled={a.actionBusy} onClick={()=>void a.friendAction(`/friends/${relation.id}`,'DELETE')}>Отменить заявку</button></>}
    </div>}
   </div>}
  </section>
 </dialog>
}
