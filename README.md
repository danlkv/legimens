
![Test](https://github.com/DaniloZZZ/legimens/workflows/Test/badge.svg?branch=master)

legimens watches for python objects in background and synchronizes
them with remote.

# Basic usage

```python
import legimens
app = legimens.App('localhost', 7000)

class Candyshop(legimens.Object):
    def __init__(self, name):
        self.name = name

shop = class Candyshop('Hello candies')


app.vars.candyshop = shop
app.start()
```

And then use your objects right away:


```js
import React, { Component } from 'react'
import Object from 'legimens';

export default class Candyshop extends Component {
    url = 'ws://localhost:7000';
    render() {
        return (
        <Object url={this.url}>
            {(data, set_data) => {

                <h1>Hello, welcome to {data.name}!</h1>
                <h2>Want some candies?</h2>
            }
        </Object>
        )
```
