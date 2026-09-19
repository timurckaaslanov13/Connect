import {useCallback,useEffect,useRef,useState} from 'react'
import {api} from './api'
export type CallState={id:string;chatId:number;targetId:number;name:string;media:'audio'|'video';phase:'incoming'|'outgoing'|'connecting'|'active';sdp?:string;started?:number}
export type Signal={type:string;call_id:string;chat_id:number;target_id:number;sender_id:number;media:'audio'|'video';sdp?:string;candidate?:RTCIceCandidateInit;reason?:string;message?:string}
export function useCall(send:(data:unknown)=>void,notify:(message:string)=>void){
  const [call,setCall]=useState<CallState|null>(null),[local,setLocal]=useState<MediaStream|null>(null),[remote,setRemote]=useState<MediaStream|null>(null)
  const [muted,setMuted]=useState(false),[cameraOff,setCameraOff]=useState(false)
  const current=useRef<CallState|null>(null),pc=useRef<RTCPeerConnection|null>(null),stream=useRef<MediaStream|null>(null),incomingIce=useRef<RTCIceCandidateInit[]>([]),outgoingIce=useRef<RTCIceCandidateInit[]>([]),canSendIce=useRef(false),timeout=useRef<ReturnType<typeof setTimeout>|undefined>(undefined)
  const update=(value:CallState|null)=>{current.current=value;setCall(value)}
  const signal=(type:string,extra:object={},active=current.current)=>{if(active)send({type,call_id:active.id,chat_id:active.chatId,target_id:active.targetId,media:active.media,...extra})}
  const clear=useCallback(()=>{
    clearTimeout(timeout.current);current.current=null;setCall(null)
    const old=pc.current;pc.current=null;if(old){old.onconnectionstatechange=null;old.onicecandidate=null;old.close()}
    stream.current?.getTracks().forEach(t=>t.stop());stream.current=null
    setLocal(null);setRemote(null);setMuted(false);setCameraOff(false);incomingIce.current=[];outgoingIce.current=[];canSendIce.current=false
  },[])
  const hangup=(reason='ended')=>{try{signal('call.end',{reason})}catch{/* connection may already be gone */}clear()}
  const fail=(error:unknown)=>{notify(error instanceof Error?error.message:'Не удалось установить звонок');hangup('failed')}
  const prepare=async(active:CallState)=>{
    if(!navigator.mediaDevices?.getUserMedia)throw new Error('Для звонка откройте Connect через HTTPS или localhost')
    let media:MediaStream
    try{media=await navigator.mediaDevices.getUserMedia({audio:true,video:active.media==='video'?{facingMode:'user',width:{ideal:1280},height:{ideal:720}}:false})}
    catch {throw new Error('Разрешите доступ к микрофону'+(active.media==='video'?' и камере':'')+' в настройках браузера')}
    if(current.current?.id!==active.id){media.getTracks().forEach(t=>t.stop());throw new Error('Звонок отменён')}
    stream.current=media;setLocal(media)
    const config=await api<RTCConfiguration>('/calls/config')
    if(current.current?.id!==active.id)throw new Error('Звонок отменён')
    const peer=new RTCPeerConnection(config);pc.current=peer
    media.getTracks().forEach(t=>peer.addTrack(t,media))
    peer.ontrack=e=>setRemote(e.streams[0]||new MediaStream([e.track]))
    peer.onicecandidate=e=>{if(e.candidate){const candidate=e.candidate.toJSON();if(canSendIce.current){try{signal('call.ice',{candidate})}catch{hangup('failed')}}else outgoingIce.current.push(candidate)}}
    peer.onconnectionstatechange=()=>{
      if(pc.current!==peer)return
      if(peer.connectionState==='connected'){clearTimeout(timeout.current);if(current.current)update({...current.current,phase:'active',started:Date.now()})}
      if(peer.connectionState==='failed'){notify('Соединение прервалось. Попробуйте позвонить ещё раз.');hangup('failed')}
      if(peer.connectionState==='disconnected'){clearTimeout(timeout.current);timeout.current=setTimeout(()=>{if(peer.connectionState!=='connected')hangup('failed')},10000)}
    }
    return peer
  }
  const flush=()=>{canSendIce.current=true;outgoingIce.current.splice(0).forEach(candidate=>signal('call.ice',{candidate}))}
  const start=async(chatId:number,targetId:number,name:string,media:'audio'|'video')=>{
    if(current.current)return
    const active:CallState={id:crypto.randomUUID(),chatId,targetId,name,media,phase:'outgoing'};update(active)
    try{const peer=await prepare(active);const offer=await peer.createOffer();await peer.setLocalDescription(offer);signal('call.invite',{sdp:offer.sdp});flush();timeout.current=setTimeout(()=>{notify('Нет ответа. Попробуйте позже.');hangup('missed')},45000)}catch(error){fail(error)}
  }
  const accept=async()=>{
    const active=current.current;if(!active||active.phase!=='incoming')return
    update({...active,phase:'connecting'});clearTimeout(timeout.current)
    try{const peer=await prepare(active);await peer.setRemoteDescription({type:'offer',sdp:active.sdp});for(const candidate of incomingIce.current.splice(0))await peer.addIceCandidate(candidate);const answer=await peer.createAnswer();await peer.setLocalDescription(answer);signal('call.answer',{sdp:answer.sdp});flush();timeout.current=setTimeout(()=>{if(current.current?.phase!=='active')fail(new Error('Не удалось соединиться. Проверьте сеть.'))},30000)}catch(error){fail(error)}
  }
  const receive=async(event:Signal,name?:string)=>{
    if(event.type==='call.invite'){
      if(current.current){send({...event,type:'call.end',target_id:event.sender_id,reason:'busy',sdp:undefined});return}
      update({id:event.call_id,chatId:event.chat_id,targetId:event.sender_id,name:name||'Входящий звонок',media:event.media,phase:'incoming',sdp:event.sdp})
      timeout.current=setTimeout(()=>hangup('missed'),45000);return
    }
    if(event.type==='call.error'){if(current.current&&(!event.call_id||event.call_id===current.current.id)){notify(event.message||'Не удалось позвонить');clear()}return}
    if(!current.current||event.call_id!==current.current.id)return
    if(event.type==='call.end'){const labels:Record<string,string>={declined:'Звонок отклонён',busy:'Пользователь занят',missed:'Пропущенный звонок',failed:'Не удалось установить соединение',ended:'Звонок завершён'};notify(labels[event.reason||'ended']||'Звонок завершён');clear();return}
    try{
      if(event.type==='call.answer' && pc.current){update({...current.current,phase:'connecting'});await pc.current.setRemoteDescription({type:'answer',sdp:event.sdp});for(const candidate of incomingIce.current.splice(0))await pc.current.addIceCandidate(candidate)}
      if(event.type==='call.ice'&&event.candidate){if(pc.current?.remoteDescription)await pc.current.addIceCandidate(event.candidate);else incomingIce.current.push(event.candidate)}
    }catch(error){fail(error)}
  }
  const toggleMic=()=>{const next=!muted;stream.current?.getAudioTracks().forEach(t=>t.enabled=!next);setMuted(next)}
  const toggleCamera=()=>{const next=!cameraOff;stream.current?.getVideoTracks().forEach(t=>t.enabled=!next);setCameraOff(next)}
  useEffect(()=>()=>clear(),[clear])
  return {call,local,remote,muted,cameraOff,start,accept,hangup,receive,toggleMic,toggleCamera,clear}
}
