import React, { useState, useEffect, useRef } from 'react'
L_ = React.createElement

import Websocket from '../websocket/Websocket.coffee'

get_ws_url = ({addr, ref}) =>
  if addr is undefined
    console.error "Legimens Widget received undefined address"
    return null
  ref = if ref then ref else ''

  [..., last] = addr
  if last!='/'
    addr = addr + '/'
  url = addr + ref
  url

###
# State machine that governs the process
###

statuses =
  dis: 'Disconnected_R3'
  wait_ref: 'Wait_Ref_R1'
  wait_var: 'Wait_Var_R*3.V*1'
  recv_ref: 'Received_Ref_R*1'
  connected: 'Connected_V*1D'
  lost_conn: 'LostConnection_V*3.V*3D'

events =
  close: 'Close'
  data: 'Message received'
  time: 'TimeTick'

###
                                                                                                                                     
R - reference websocket
1 - websocket opened
3 - websocket closed
* - received root ref
D - received Data

/event/
action()


                                                                                                                                     
                                                                                                                                     
                  +-------------+      /data/    +--------------+                                                                    
   openWs() ----- |     R1      ----------------->      R*1     |---- colseWs()                                                      
                  |  Wait ref   |                | Received ref |     cancelTimer()                                                  
                  +------^------+                +-------|------+                                                                    
                         |   |                           |                                                                           
                  /time/ |   | /close/                   | /close/                                                                   
                         |   |                           |                                                                           
                         |   v                           |                                                                           
                  +-------------+     /close/    +-------v------+                                                                    
  setTimer() ---- |     R3      <-----------------  R*3 V*1 V0  |--- openWs()                                                        
                  |  Disconnect |                |   Wait vars  |                                                                    
                  +------^------+                +-------|------+                                                                    
                         |                               |                                                                           
                  /time/ |                               | /data/                                                                    
                         |                               |                                                                           
                         |                               |                                                                           
                 +---------------+    /close/    +-------v------+                                                                    
  reRender() --- |   V*3 V*3D    <----------------     V*1D     <-----  reRender()                                                   
                 |   Lost conn   |               |   Connected  |    ^                                                               
                 +---------------+               +-------|------+    |                                                               
                                                         |  /data/   |                                                               
                                                         v           |                                                               
                                                         ------------>                    

###

get_next_status = (event, status)=>
  if status == statuses.dis
    if event == events.time
      return statuses.wait_ref
    else
      return statuses.dis

  else if status == statuses.wait_ref
    if event == events.close
      return statuses.dis
    else if event == events.data
      return statuses.recv_ref
    else
      return statuses.wait_ref ## This should not be reached

  else if status == statuses.recv_ref
    if event == events.close
      return statuses.wait_var
    else if event == events.data
      console.log 'Got data in closed state. Investigate.'
      return statuses.wait_var ## Why did we get data in cosed state?
    else
      return statuses.wait_var ## Why did we get data in cosed state?

  else if status == statuses.wait_var
    if event == events.close
      console.log 'Failed to retreive variables'
      return statuses.dis
    else if event == events.data
      return statuses.connected
    else
      return statuses.wait_var
  else if status == statuses.connected
    if event == events.close
      return statuses.lost_conn
    else if event == events.data
      return statuses.connected

  else if status == statuses.lost_conn
    if event == events.time
      return statuses.dis
    else if event == events.data
      console.log("Wierd: we lost connection, but retreived data")
      return statuses.dis
  return status


get_next_state = (event, state) =>
  {addr, data, status} = state
  next_status = get_next_status event, status
  console.log 'prevstatus', status, 'next status', next_status
  if next_status == statuses.wait_ref
    next_ws_url = get_ws_url {addr, ref:''}
  else if next_status == statuses.wait_var
    next_ws_url = get_ws_url {addr, ref:data.root}
  return {addr, data, status:next_status, ws_url:next_ws_url}


statusActionMap =
  [statuses.dis]: ['setTimer']
  [statuses.wait_ref]: ['openWs']
  [statuses.recv_ref]: ['closeWs', 'cancelTimer']
  [statuses.wait_var]: ['openWs']
  [statuses.connected]: ['reRender']
  [statuses.lost_conn]: ['setTimer']


on_event = ({event, state, setState, actionsMap}) =>
  console.log 'on event', event, 'new state', state
  new_state = get_next_state event, state
  console.log 'next state', new_state
  setState new_state
  actions = statusActionMap[new_state.status]
  for actionKey in actions
    action = actionsMap[actionKey]
    success = action()
  return

# Hooks


###
# Hooks to use Legimens in React
###

export useLegimensRoot = ({addr})=>
  [vars, setVars] = useState()
  stateRef = useRef {addr, status:statuses.dis, ws_url:'', data:{} }
  setState = (state)=>
    stateRef.current = state
  state = stateRef.current
  timerDelay = 2600

  wsRef = useRef()
  timerRef = useRef()
  actions =
    setTimer: ()=>
      timerRef.current = setTimeout ()=>
        state = stateRef.current
        on_event {event:events.time, state, setState, actionsMap:actions}
      ,
        timerDelay
    cancelTimer: ()=>
      clearTimeout timerRef.current
    openWs: ()=>
      state = stateRef.current
      console.log 'opening websocket. state.ws_url=', state.ws_url
      wsRef.current = new WebSocket state.ws_url
      wsRef.current.onclose = ()=>
        state = stateRef.current
        on_event {event:events.close, state, setState, actionsMap:actions}
      wsRef.current.onmessage = (message)=>
        state = stateRef.current
        data = JSON.parse message.data
        state.data = data
        on_event {event:events.data, state, setState, actionsMap:actions}
    closeWs: ()=>
      wsRef.current.close 1000
    reRender: ()=>
      console.log 'Triggering re-render'
      state = stateRef.current
      setVars {state.data...}

  if state.status== statuses.dis
    on_event {event:events.time, state, setState, actionsMap:actions}
  statusret = {connected: state.status == statuses.connected}
  return {data:vars, status:statusret}


export default useLegimens = ({addr, ref, timerTck})=>
  [status, setStatus] = useState connected:false, opened: false
  [data, setData] = useState {}
  [respond, setRespond] = useState null

  #prevaddr = usePrevious addr, 'addr'
  #prevref = usePrevious ref, 'ref'
  #prevdata = usePrevious data, 'data'
  #prevstatus = usePrevious status, 'status'
  wsUrlRef = useRef(null)
  ws_url = get_ws_url {addr, ref}
  if wsUrlRef.current and (wsUrlRef.current != ws_url)
    console.log 'resetting data, changed addr'
    data = {}
  wsUrlRef.current = ws_url

  useEffect ()=>
    setData {}
    try
      ws = new WebSocket ws_url
      setStatus connected:false, opened:false
    catch e
      setStatus error:e, connected:false, opened: false

    if ws
      console.debug('after ws create', ws)
      ws.addEventListener 'error', (e)=>
        console.error e
        setStatus connected:false, error:e
      ws.addEventListener 'message', (msgData) =>
        #console.log 'messag', msgData, ws
        setData JSON.parse msgData.data
      ws.addEventListener 'open', ()=>
        console.log 'opened connection', ws_url, ws
        setStatus connected:true, opened:true
      ws.addEventListener 'close', (e)=>
        console.log 'closing connection', ws_url, e, ws
        setStatus connected:false, opened:true

      setRespond ()=>(resp)=>
        console.log 'sendind response', resp
        ws.send resp

    return ()=> ws?.close 1000
  , [ws_url, timerTck]
  return {data, status, respond}



usePrevious = (value, name)=>
  ref = useRef()
  useEffect () =>
    ref.current = value
    return undefined
  ,
    [value]
  console.log "logPrevious: value of #{name}. Current=", value, "Previous=", ref.current
  return ref.current
