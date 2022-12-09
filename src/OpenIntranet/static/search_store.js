/**
 * RECOMANDED USAGE
 * 
 * // insert modal to html
 * const modal = new ProductSelectionModal();
 * 
 * // show modal to user 
 * modal.showModal()
 * 
 * // setup event for product selection completition
 * $(".selection-confirm-button").click(function() {
 *    // store selected value where you like
 *    const id_of_selected_product = modal.getID();
    })
 */
const DEFAULT_IMG = "/static/img/image-alt.svg";
const MODAL = `
    <!-- Modal -->
    <div id="productSelectionModal" class="modal fade" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
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
          </div> <!-- modal footer -->
        </div> <!-- modal content -->
      </div> <!-- modal dialog -->
    </div> <!-- modal -->`;

// based on searchbar content
function searchForCorespondingProducts() {
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

        const img_url = (value.img_title == null || value.img_title.url == null) ? DEFAULT_IMG : value.img_title.url;
        let desc = value.description ? value.description : "";
        if (desc.length > 120) {
          desc = desc.substring(0,100)+' ...';
        }
        
        $('#coresponding-products').append(
          `<div id="` + value._id.$oid + `" class="coresponding-product card mb-3" style="max-width: 540px;">
            <div class="row g-0">
              <div class="col-md-4">
                <img class="img-thumbnail" style="width:100%; " src="`+img_url+`"> 
              </div>
              <div class="col-md-8">
                <div class="card-body">
                  <a href="`+ "/store/component/" + value._id.$oid + `" class="card-title fs-3">` + value.name + `</a>
                  <h6 class="card-subtitle mb-2 text-muted">ID: `+ value._id.$oid + `</h6>
                  <p class="card-text">`+ desc + `</p>
                </div>

                <div class="card-footer">
                  <button type="button" data-bs-dismiss="modal" class="selection-confirm-button btn btn-success">Zvolit součástku</button>
                </div>

              </div>
            </div>
          </div>`);
      });

      $(".selection-confirm-button").click(function(){
        let id = $(this).closest('.coresponding-product').attr('id');
        this.id = id;
      });
    },
    error: function (jqXhr, textStatus, errorThrown) {
      console.log('ERR, /store/api/products/');
      console.log(errorThrown);
    }
  });
}

class ProductSelectionModal {
  
  // initialize hidden modal in current document
  constructor() {
    // id of selected product
    this.id = null;
    $("body").append(MODAL);

    $('#productNameInput').keyup(function(e){
      if(e.keyCode == 13) { 
        searchForCorespondingProducts(); }
    });

    $('#searchButton').click(searchForCorespondingProducts)
  }
  
  showModal() {
    $("#productSelectionModal").modal("show");
    $("#loading-products-container").hide();
  }

  setId(newId) {
    this.id = newId;
  }

  getId() {
    return this.id;
  }

  getSelectedProduct() {
    return this.id != null ? idToProduct(this.id) : null;
  }
}
