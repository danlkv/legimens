import React, { Component } from 'react'
import L from 'react-dom-factories'
import Object from './hosta/Object.coffee'
import WebSocket from './websocket/Websocket.coffee'
L_ = React.createElement
import './App.less'

Greeting = ({name})->
  L.div className:'greeting',
    L.h2 style:textAlign:'center', "Hello, #{name}"

class Greet extends Component
  state : { value:'a' }
  change:(e)=>
    value = e.target.value
    @setState {value}
    @props.onChange value
  render: ->
    L.div className:'gret',
      L.div className:'greet',"Hello, #{@props.name}"
      L.input
        type:'text'
        value:@state.value
        onChange:(e)=>@change e


export default class App extends Component
  state : {
    value:'ws://localhost:8082/'
  }
  constructor:(props)->
    super(props)
     
  render: ->
    L.div className:'app',
      L.input
        type:'text',
        value: @state.value
        onChange:({target:value:value})=>@setState {value}
      L_ WebSocket, url:@state.value,
        (data, reply)->
          L_ Greet, name:data, onChange:reply

