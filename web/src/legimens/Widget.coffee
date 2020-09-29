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

export default useLegimensWithTimer = ({addr, ref})=>
  [tick, setTick] = useState 0
  console.log 'useref'
  timerRef = useRef()
  ret = useLegimens {addr, ref, timerTck:tick}
  if not ret.status.connected
    if not timerRef.current
      console.log 'setti'
      timerRef.current = setTimeout ()=>
        setTick((t)=>
          console.log t
          timerRef.current = null
          t+1)
      ,
        2000
  else
    if timerRef.current
      clearTimeout timerRef.current
      console.log 'clearTimeout'
      timerRef.current = null
  return ret


export useLegimens = ({addr, ref, timerTck})=>
  [data, setData] = useState {}
  [status, setStatus] = useState connected:false, opened: false
  [respond, setRespond] = useState null
  ws_url = get_ws_url {addr, ref}
  useEffect ()=>
    console.debug('before ws create', ws)
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
        console.log 'messag', msgData, ws
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


export useLegimensRoot = ({addr, ref})=>
  [rootRef, setRootRef] = useState null
  [vardata, setVardata] = useState {}

  if not rootRef
    rootLeg = useLegimensWithTimer addr:addr, ref:''
    handshaked = rootLeg.status.connected and rootLeg.data.root
    if not handshaked
      data = vardata
      status = connected:false, opened:false
      respond = null
      return {data, status, respond}

    setRootRef rootLeg.data.root
    data = vardata
    status = connected:false
    respond = null
    return {data, status, respond}

  else
    console.log 'RootRef', rootRef
    varLeg = useLegimensWithTimer addr:addr, ref:rootRef
    console.log 'varleg', varLeg
    if varLeg.status.opened and not varLeg.status.connected
      console.log 'Lost connection!'
      setVardata varLeg.data
      setRootRef null
    return varLeg
