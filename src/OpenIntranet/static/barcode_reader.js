

class barcode_reader{
    constructor(address = "ws://localhost:8765/ws") {
        this.address = address;
        this.callback = {};
        this.solo = null;
        this.ws = null

        if ("WebSocket" in window) {
           this.ws = new WebSocket(this.address);
           this.ws.onopen = function() {
              console.log("opened...")
              $("[type = barcodereader-icon]").removeAttr('class');
              $("[type = barcodereader-icon]").attr('class', 'bi bi-upc-scan');
           };

           var self = this;
           this.ws.onmessage = function(evt) {
             console.log("[CODE_READER] ",evt);
             self.doCallback(JSON.parse(evt.data));
           };

           this.ws.onclose = function() {
              console.log("Barcode reader is disconected....");
              //$('.barcode-icon').text('phonelink_erase');              
              $("[type = barcodereader-icon]").removeAttr('class');
              $("[type = barcodereader-icon]").attr('class', 'bi bi-x-lg');
           };

        } else {
           alert("WebSocket NOT supported by your Browser!");
        }
    }

    onMessage(evt){
        console.log("OWN LOG PARSER", evt);
    }

    doCallback(data){
        console.log("CALLBACK", data);
        for(var callback in this.callback){
            var callback_info = this.callback[callback];
            console.log(callback_info);
            callback_info.callback(data);
            
        }
    }

    setSolo(name){
        if(name in this.callback){
            this.solo = name;
            return true;
        }else{
            return false;
        }
    }

    getCallbacks(){
        console.log("GET CALLBACK...");
        return this.callback;
    }

    addCallback(name, callback, type = null, group = null, codetype = null){
        if (this.callback[name] === undefined){
            this.callback[name] = {};
        }
        this.callback[name]['callback'] = callback;
        this.callback[name]['type'] = type;
        this.callback[name]['group'] = group;
        this.callback[name]['active'] = true;
        this.callback[name]['codetype'] = codetype;
    }

    activateCallback(name, activate = true){
        if (this.callback[name] === undefined){
            return false;
        }
        this.callback[name]['active'] = active;
    }
}


function BC_store_OpenArticleEdit(data){
    $('#modal-edit-component').modal('hide');
    OpenArticleEdit(data['code']);
}

function BC_store_LoadProduct(data){

}
