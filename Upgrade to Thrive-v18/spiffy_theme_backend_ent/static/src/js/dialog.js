/** @thrive-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { useEffect } from "@thrive/owl";
import { patch } from "@web/core/utils/patch";

patch(Dialog.prototype, {
    /**
     *
     * @override
     */
    setup() {
        super.setup();
        // MAKE ANY MODAL DRAGGABLE
        useEffect(
            (el) => {
                if (el) {
                    let $modal = $(el);
                    $($modal).find('.modal-dialog').draggable({
                        handle: ".modal-header",
                    });
                    var width = $modal.find('.modal-content').width();
                    var height = $modal.find('.modal-content').height();
                    var backdrop = $modal.attr('data-backdrop');
                    if (backdrop){
                        $('body.modal-open').attr('data-backdrop', backdrop);
                    }
                    $modal.find('.modal-content').resizable({
                        minWidth: width,
                        minHeight: height,
                    });
                }
            },
            () => [this.modalRef.el]
        );
    }
});
