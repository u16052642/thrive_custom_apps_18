/** @thrive-module **/

import { patch } from "@web/core/utils/patch";
import { session } from '@web/session';
import { FormController } from "@web/views/form/form_controller";
import { FormStatusIndicator } from "@web/views/form/form_status_indicator/form_status_indicator";
import {onMounted,onPatched,} from "@thrive/owl";

console.log("session.session", session);

patch(FormController.prototype, {
    setup(){
        super.setup();
        onMounted(() => {
            $('div.o_attachment_preview').length > 0 ? $('body').addClass('hasAttachment') : $('body').removeClass('hasAttachment');
        });
        onPatched(() => {
            $('div.o_attachment_preview').length > 0 ? $('body').addClass('hasAttachment') : $('body').removeClass('hasAttachment');
        });
    },

    async onPagerUpdate({ offset, resIds }) {
        const dirty = await this.model.root.isDirty();
        if (dirty) {
            if ($('body').hasClass('prevent_auto_save')){
                return this.model.root.discard();
            } else {
                return this.model.root.save({
                    onError: this.onSaveError.bind(this),
                    nextId: resIds[offset],
                });
            }
            
        } else {
            return this.model.load({ resId: resIds[offset] });
        }
    },

    async beforeLeave() {
        if (this.model.root.dirty) {
            if ($('body').hasClass('prevent_auto_save')){
                return this.model.root.discard();
            } else {
                return this.model.root.save({
                    reload: false,
                    onError: this.onSaveError.bind(this),
                });
            }
        }
    }
});

patch(FormStatusIndicator.prototype, {
    get displayAutoSavePrevent() {
        return Boolean($('body').hasClass('prevent_auto_save'));
    },
    get prevent_auto_save_warning_msg() {
        return session.prevent_auto_save_warning_msg
    },
});