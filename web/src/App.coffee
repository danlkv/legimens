import React, { Component } from 'react'
import L from 'react-dom-factories'
import Object from './hosta/Object.coffee'
import WebSocket from './helpers/WS.coffee'
L_ = React.createElement
import './App.less'

Greeting = ({name})->
  L.div className:'greeting',
    L.h2 style:textAlign:'center', "Hello, #{name}"

class Greet extends Component
  constructor:(props)->
    super props
  render: ->
    L.div className:'greet',"Hello, #{@props.name}"


export default class App extends Component
  constructor:(props)->
    super(props)
     
  render: ->
    L.div className:'app',
      L_ WebSocket, url:'ws://localhost:7700',
        (data)->
          L_ Greet, name:data

