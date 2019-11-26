import React, { Component } from 'react'
import L from 'react-dom-factories'
L_ = React.createElement
import './App.less'

Greeting = ()->
  L.div className:'greeting',
    L.h2 style:textAlign:'center', 'Hello World'

export default class App extends React.Component
  constructor:->
    super()
     
  render: ->
    L.div className:'app',
      L_ Greeting, null

