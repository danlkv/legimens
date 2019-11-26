# Build your apps fast!

```python
import hosta

class Candyshop(hosta.Object):
    def __init__(self, name):
        self.name = name

shop = class Candyshop('Hello candies')


app = hosta.app('localhost:7000')
app.host(shop)
app.start()
```

And then use your objects right away:

```js
import {Object} from 'hosta';

export default class Candyshop extends Object {
    address = 'localhost:7000';
    render() {
        return (
        <div>
            <h1>Hello, welcome to {this.props.name}!</h1>
            <h2>Want some candies?</h2>
        </div>
        )
```
