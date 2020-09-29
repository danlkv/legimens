import React, { useState, useEffect } from 'react'
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


export default useLegimens = ({addr, ref})=>
  [data, setData] = useState {}
  [status, setStatus] = useState connected:false
  [respond, setRespond] = useState null
  ws_url = get_ws_url {addr, ref}
  useEffect ()=>
    console.debug('before ws create', ws)
    try
      ws = new WebSocket ws_url
    catch e
      setStatus error:e, connected:false

    if ws
      console.debug('after ws create', ws)
      ws.addEventListener 'error', (e)=>
        console.error e
        setStatus connected:false, error:e
      ws.addEventListener 'message', (msgData) =>
        setData JSON.parse msgData.data
      ws.addEventListener 'open', ()=>
        console.log 'opened connection', ws_url, ws
        setStatus connected:true
      ws.addEventListener 'close', (e)=>
        console.log 'closing connection', ws_url, e, ws
        setStatus connected:false

      setRespond ()=>(resp)=>
        console.log 'sendind response', resp
        ws.send resp

    return ()=> ws?.close 1000
  , [ws_url]
  return {data, status, respond}

export useLegimensRoot = ({addr, ref})=>
  [rootRef, setRootRef] = useState null

  if not rootRef
    rootLeg = useLegimens addr:addr, ref:''
    handshaked = rootLeg.status.connected and rootLeg.data.root
    if not handshaked
      data = {}
      status = connected:false
      respond = null
      return {data, status, respond}

    setRootRef rootLeg.data.root
    data = {}
    status = connected:false
    respond = null
    return {data, status, respond}

  else
    console.log 'RootRef', rootRef
    varLeg = useLegimens addr:addr, ref:rootRef
    return varLeg
