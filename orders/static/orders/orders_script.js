// Overwrite parseResult() from menu_script to suit shopping_cart.html
function parseResult(resp, elements) {
  document.getElementById('food-cost').textContent = resp.new_cost
  elements['cart_cost'].textContent = resp.new_cost
  let item_price = elements['menu_item'].getElementsByClassName('item-price')[0]
  let item_cost = elements['menu_item'].getElementsByClassName('item-cost')[0]
  item_cost.textContent = item_price.textContent * elements['current_amount'].textContent

  if (item_cost.textContent === '0') {
    console.log(elements['menu_item'])
    let list_item = elements['menu_item'].remove()
  };
};
