import React, { Component } from 'react'
L_ = React.createElement

import Websocket from '../websocket/Websocket.coffee'

export default class Object extends Component
  constructor:(props) ->
    super props
    console.log 5
    @name = @constructor.name
    @object_props = {}

  render: ->
    {refval, addr} = @props
    console.log("object render",@props)
    url = addr + refval
    L_ Websocket, url:url, (data, update) =>
      setAttr = (attr, value) ->
        update JSON.stringify [attr]:value
      if not data
        data = '{}'
      data = JSON.parse data
      @object_props = {@object_props..., data...}
      @props.children @object_props, setAttr
