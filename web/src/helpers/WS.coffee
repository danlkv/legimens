import WS from 'react-websocket'
import React, { Component } from 'react'

export default class WebSocket extends Component
  state = {}
  constructor:(props) ->
    super props
    @state = {}
    console.log("children",@props.children)

  onMessage:(data) =>
    try
      data = JSON.parse data
    catch
    @setState {data}

  render: =>
    <div>
      {@props.children(@state.data)}
      <WS url={@props.url} onMessage={@onMessage}/>
    </div>

