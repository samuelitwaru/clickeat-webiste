$(".number-input").val("1")
.keypress((e)=>{
	return false
})
.change((e)=>{
	var target = e.target.dataset.target
	$(target).html($(e.target).val())
}).hide()

$('.number-input-plus, .number-input-minus').click((e)=>{
	var numberInput = e.target.dataset.numberInput
	var value = 0
	var min = parseInt($(numberInput).attr('min'))-1
	var max = parseInt($(numberInput).attr('max'))+1
	if($(e.target).hasClass('number-input-plus')){value++}else if($(e.target).hasClass('number-input-minus')){value-=1}
	var newVal = parseInt($(numberInput).val())+value
	if ((min&&newVal<min)||(max&&newVal>max)){return}
	$(numberInput).val(min<newVal&newVal<max?newVal:newVal-value).change()

})