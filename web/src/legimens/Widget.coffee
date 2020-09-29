import React, { Component } from 'react'
L_ = React.createElement

import Websocket from '../websocket/Websocket.coffee'

export default class Object extends Component
  constructor:(props) ->
    super props
    @object_props = {}

  get_url:()->
    {refval, addr} = @props
    [..., last] = addr
    if last!='/'
      addr = addr + '/'
    url = addr + refval
    url

  render: ->
    url = @get_url()
    L_ Websocket,
      url:url
      onClose: @props.onClose
      onOpen: @props.onOpen
      onError: @props.onError
      (data, update) =>
        setAttr = (attr, value) ->
          update JSON.stringify [attr]:value
        if not data
          data = '{}'
        data = JSON.parse data
        if @props.cache
          @object_props = {@object_props..., data...}
        else
          @object_props = data
        @props.children @object_props, setAttr
