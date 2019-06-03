const AMOUNT_CHANGE = {
  'increase': 1,
  'decrease': -1
}

document.addEventListener("DOMContentLoaded", function() {
  for (let button of document.getElementsByClassName('change-amount')) {
    button.addEventListener('click', updateCart)
  };
});

function updateCart(e) {

  let amount_container = e.target.parentNode
  let current_amount = amount_container.getElementsByClassName('current_amount')[0]

  let last_amount = Number(current_amount.textContent)
  let action = e.target.dataset.action

  let new_amount
  if (action === 'remove') {
    new_amount = 0
  } else {
    new_amount = last_amount + AMOUNT_CHANGE[action]
    if (new_amount < 0) {
      return
    }
  }
  current_amount.textContent = new_amount
  item_id = current_amount.dataset.item_id

  query = {'item_id': item_id,'action': action}
  // update_cart_url set on Django template
  final_url = update_cart_url + '?' + encodeQueryData(query)
  let updateRequest = new Request(final_url)

  fetch(updateRequest).then(function(response) {
    if (response.ok) {
      return response.json()
    }
    throw new Error('Incorrect amount or action.');
  }).then(function(responseJson) {
    let elements = {
      'cart_cost': document.getElementById('cart-cost'),
      'amount_container': amount_container,
      'current_amount': current_amount,
    }
    parseResult(responseJson, elements)
  }).catch(function(error) {
    // TODO do i need to pass current_amount and last_amount?
    handleError(error);
  });
};

function parseResult(resp, elements) {
    elements['cart_cost'].textContent = resp.new_cost
};

function encodeQueryData(data) {
  // https://stackoverflow.com/a/111545
  const ret = [];
  for (let d in data)
    ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
  return ret.join('&');
};

function handleError(error) {
  console.log('There has been a problem with your fetch operation: ', error.message);

  // set amount value to last_amount and show an error message
  current_amount.textContent = last_amount

  if (!document.getElementById('error_div')) {
    let error_div = document.createElement('div')
    error_div.id = 'error_div'
    current_amount.parentElement.appendChild(error_div)

    let close_button = document.createElement('button')
    close_button.textContent = 'Close'
    current_amount.parentElement.appendChild(close_button)

    close_button.addEventListener('click', () => {
      current_amount.parentElement.removeChild(error_div)
      current_amount.parentElement.removeChild(close_button)
    })
  }
  document.getElementById('error_div').textContent = error.message
};
