import React, { Component } from 'react'
import L from 'react-dom-factories'

export default class WebSock extends Component
  _init_ws:({url, onOpen, onClose, onError})->
    try
      @ws = new WebSocket url
    catch e
      @onError? e
    console.debug 'constructor ws', @props
    @ws.addEventListener 'message', @onMessage
    @ws.addEventListener 'open', onOpen
    @ws.addEventListener 'close', @onClose
    @ws.addEventListener 'error', @onError

  onMessage: (message)=>
    console.debug('message', message)
    @setState {message}

  onError: (error)=>
    console.debug('error', error)
    @setState message:{}
    @props.onError? err

  onClose: (e)=>
    console.debug('close', e, @props, @)
    @setState message:{}
    @props.onClose?(e)

  send: (message) =>
    @ws.send message

  componentWillUnmount: ()=>
    console.debug('will unmount')
    @ws.close()
    @ws = null

  render:()->
    # Handle updated props
    console.debug('legimens render', @props)
    if @props.url != @ws?.url
      try
        @ws?.close 1000
      catch e
        console.log e
      @_init_ws @props
    @props.children @state?.message.data, @send
