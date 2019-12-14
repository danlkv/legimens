import React, { Component } from 'react'
import L from 'react-dom-factories'

export default class WebSock extends Component
  state = {}
  constructor:(props) ->
    super(props)
    console.log("constructor")

  _init_ws:({url, onOpen, onClose, onError})->
    @ws = new WebSocket url
    @ws.addEventListener 'message', @onMessage
    @ws.addEventListener 'open', onOpen
    @ws.addEventListener 'close', onClose
    @ws.addEventListener 'error', onError

  onMessage: (message)=>
    @setState {message}

  send: (message) =>
    console.log("Sending", message)
    @ws.send message

  render:()->
    if @props.url != @ws?.url
      @_init_ws @props
    @props.children @state?.message.data, @send




