// menu list has covering element
document.addEventListener("DOMContentLoaded", function() {
  for (let current_amount of document.getElementsByClassName('current-amount')) {
    updateVisible(current_amount);
  };
});

function updateVisible(current_amount) {
  let method = Number(current_amount.textContent) !== 0 ? 'add' : 'remove'
  current_amount.closest('.item-amount').classList[method]('upper')
};

function parseResult(resp, elements) {
  elements['cart_cost'].textContent = resp.new_cost
  updateVisible(elements['current_amount'])
};
