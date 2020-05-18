import React, { Component } from 'react'
L_ = React.createElement

import Websocket from '../websocket/Websocket.coffee'

export default class Object extends Component
  constructor:(props) ->
    super props
    @object_props = {}

  render: ->
    {refval, addr} = @props
    [..., last] = addr
    if last!='/'
      addr = addr + '/'
    url = addr + refval
    L_ Websocket, url:url, (data, update) =>
      setAttr = (attr, value) ->
        update JSON.stringify [attr]:value
      if not data
        data = '{}'
      data = JSON.parse data
      @object_props = {@object_props..., data...}
      @props.children @object_props, setAttr
