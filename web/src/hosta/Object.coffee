import React, { Component } from 'react'
L_ = React.createElement

import Websocket from '../websocket/Websocket.coffee'

export default class Object extends Component
  constructor:(props) ->
    super props
    @name = @constructor.name

  render: ->
    {refval, addr} = @props
    console.log(".",@props)
    url = addr + refval

    L_ Websocket, url:url, (data, update) =>
      setAttr = (attr, value) ->
        update JSON.stringify [attr]:value

      @props.children data, setAttr
