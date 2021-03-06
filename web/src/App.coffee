import React, { Component } from 'react'
import L from 'react-dom-factories'
import Object from './legimens/Object.coffee'
import Websocket from './websocket/Websocket.coffee'
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
        onChange:({target:value:value}) => @setState {value}
      L_ Object, addr:@state.value, refval:'',
        (data, setattr)->
          change = (value)=>
            setattr 'value', value
          L_ Greet, name:JSON.stringify(data), onChange:change

