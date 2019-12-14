class Base{
    constructor(){
    }
    my_name(){
        console.log("Inside Base: My name is",String(this.constructor.name));
    }
}

class Test extends Base{
    constructor(){
        super()
        console.log("Inside test constructor")
    }
}

test = new Test()
test.my_name()

