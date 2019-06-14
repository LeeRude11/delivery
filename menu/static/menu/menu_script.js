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

  let amount_container = e.currentTarget.closest('.item-amount')
  let current_amount = amount_container.getElementsByClassName('current-amount')[0]

  let last_amount_num = Number(current_amount.textContent)
  let action = e.currentTarget.dataset.action

  let new_amount
  if (action === 'remove') {
    new_amount = 0
  } else {
    new_amount = last_amount_num + AMOUNT_CHANGE[action]
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
    // set amount to previous and show an error
    current_amount.textContent = last_amount_num
    showError(error, amount_container);
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

function showError(error, container) {
  console.log('There has been a problem with your fetch operation: ', error.message);

  if (!document.getElementById('error-div')) {
    let error_div = document.createElement('div')
    error_div.id = 'error-div'
    container.appendChild(error_div)

    let error_text_span = document.createElement('span')
    error_text_span.id = 'error-text'
    error_div.appendChild(error_text_span)

    let close_button = document.createElement('button')
    close_button.textContent = 'Close'
    error_div.appendChild(close_button)

    close_button.addEventListener('click', () => {
      container.removeChild(error_div)
    })
  }
  document.getElementById('error-text').textContent = error.message
};
