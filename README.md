
```flow
st=>start: run loop
op=>operation: My Operation
cond=>condition: IP assigned?

st->op->cond
cond(yes)->e
cond(no)->op
```
```flow
st=>start: Start
e=>end
op=>operation: My Operation
cond=>condition: Yes or No?

st->op->cond
cond(yes)->e
cond(no)->op
```
> Written with [StackEdit](https://stackedit.io/).