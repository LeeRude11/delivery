// Overwrite parseResult() from menu_script to suit shopping_cart.html
function parseResult(resp, elements) {
  document.getElementById('food_cost').textContent = resp.new_cost
  elements['cart_cost'].textContent = resp.new_cost
  let item_price = elements['amount_container'].getElementsByClassName('item_price')[0]
  let item_cost = elements['amount_container'].getElementsByClassName('item_cost')[0]
  item_cost.textContent = item_price.textContent * elements['current_amount'].textContent

  if (item_cost.textContent === '0') {
    let list_item = elements['amount_container'].parentNode
    list_item.parentNode.removeChild(list_item)
  };
};
