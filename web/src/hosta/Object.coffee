import React, { Component } from 'react'

#export default Object = (C)=> class extends C {
export default class Object extends Component
  constructor:(props) ->
    super props
    @name = @constructor.name
  bar: ->
    console.log("Inside s")
  render: ->
    L.div className:'d', 'hello'
