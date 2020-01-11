import React, { Component } from 'react'
import L from 'react-dom-factories'

export default class WebSock extends Component
  state = {}
  constructor:(props) ->
    super(props)
    console.log 'websocket constructor', props

  _init_ws:({url, onOpen, onClose, onError})->
    @ws = new WebSocket url
    @ws.addEventListener 'message', @onMessage
    @ws.addEventListener 'open', onOpen
    @ws.addEventListener 'close', onClose
    @ws.addEventListener 'error', onError

  onMessage: (message)=>
    @setState {message}

  send: (message) =>
    @ws.send message

  render:()->
    # Handle updated props
    if @props.url != @ws?.url
      @ws?.close 1000
      @_init_ws @props
    @props.children @state?.message.data, @send




