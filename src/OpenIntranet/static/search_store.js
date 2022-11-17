/**
 * RECOMANDED USAGE
 * 
 * // run modal
 * search_product_id()
 * 
 * // setup event for product selection completition
 * $("#selection-confirm-button").click(function() {
      // store selected value where you like
      const id_of_selected_product = $(".coresponding-product.selected").attr('id');
    })
 */

/**
 * get product from store corresponding to search
 * - run modal with search bar
 * - user types phrase (name of product)
 * - user confirms selection
 * - extraction of id is described in the header of this file
 */
 function search_product_id() {
  $(document).ready(function () {
    let modal = `
  <!-- Modal -->
  <div id="myModal" class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="exampleModalLabel">skladové součástky</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div> <!-- modal header -->
        <div class="modal-body">
          <div class="input-group mb-3">
            <input id="productNameInput" type="text" class="form-control"
            placeholder="Název součástky" aria-label="Název součástky" aria-describedby="button-addon2">
            <button class="btn btn-outline-secondary" type="button" id="searchButton">Vyhledej</button>
    
          </div>
          <!-- list of products found -->
          <div id="coresponding-products" class="container">
            <div id="loading-products-container">
              <div class="d-flex mt-3 align-items-center">
                <strong>Hledám součástky...</strong>
                <div class="spinner-border ms-auto" role="status" aria-hidden="true"></div>
              </div>
            </div>
          </div>
        </div> <!-- modal body -->

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zrušit</button>
          <button id="selection-confirm-button" type="button" class="btn btn-primary">Potvrdit výběr</button>
        </div> <!-- modal footer -->
      </div> <!-- modal content -->
    </div> <!-- modal dialog -->
  </div> <!-- modal -->`

    $("body").append(modal);
    $("#myModal").modal("show");
    $("#loading-products-container").hide();

    $('#searchButton').click(function () {
      $("#loading-products-container").show();

      const search_phrase = $("#productNameInput").val();


      $.ajax({
        type: "POST",
        url: "/store/api/products/",
        data: {
          'categories': "0", // 0 == false
          'search_by_category': "0", // 0 == False
          //   'positions': active_positions(),
          'search_by_position': "0", // 0 == False
          'search': search_phrase,
          'polarity': false,
          'tag_polarity': false,
          // 'tag_search': $("#tag-search").val(),
          //   'in_stock': $("#filter-instock").val(),
          'page': 0
        },
        success: function (data, textStatus, jQxhr) {
          console.log('/products/', data, textStatus);
          const num_of_items_found = data.count;

          $('#coresponding-products').empty();
          Object.values(data.data).forEach((value, idx, arr) => {

            $('#coresponding-products').append(
              `<div id="` + value._id.$oid + `" class="coresponding-product card mb-3" style="max-width: 540px;">
                <div class="row g-0">
                  <div class="col-md-4">
                    <img class="img-thumbnail" src="...image url here..." alt="W3Schools.com"> 
                  </div>
                  <div class="col-md-8">
                    <div class="card-body">
                      <a href="`+ "/store/component/" + value._id.$oid + `" class="card-title">` + value.name + `</a>
                      <h6 class="card-subtitle mb-2 text-muted">ID: `+ value._id.$oid + `</h6>
                      <p class="card-text">`+ value.description + `</p>
                    </div>
                  </div>
                </div>
              </div>`);
          })

          $(".coresponding-product").click(function(){
            $("#coresponding-products").children().each(function() {
              $(this).removeClass('selected border-success');
            })
            $(this).addClass('selected border-success');
          })
        },
        error: function (jqXhr, textStatus, errorThrown) {
          console.log('ERR, /store/api/products/')
          console.log(errorThrown);
        }
      });
    })
  });
}