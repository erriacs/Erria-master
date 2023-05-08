odoo.define('ecs_repair.BasicModel', function (require) {
	
	var BasicModel = require('web.BasicModel');
	var NewBasicModel = BasicModel.include({
		_isX2ManyValid: function (id) {
	        var self = this;
	        var isValid = true;
	        var element = this.localData[id];
	        _.each(element._changes, function (command) {
	            if (command.operation === 'DELETE' ||
	                    command.operation === 'FORGET' ||
	                    (command.operation === 'ADD' &&  !command.isNew)||
	                    command.operation === 'REMOVE_ALL') {
	                return;
	            }
	            var recordData = self.get(command.id, {raw: true}).data;
	            var record = self.localData[command.id];
	            _.each(element.getFieldNames(), function (fieldName) {
	                var field = element.fields[fieldName];
	                var fieldInfo = element.fieldsInfo[element.viewType][fieldName];
	                var rawModifiers = fieldInfo.modifiers || {};
	                var modifiers = self._evalModifiers(record, rawModifiers);
	                if(recordData[fieldName]){
	                    if (modifiers.required && !self._isFieldSet(recordData[fieldName], field.type)) {
	                        isValid = false;
	                    }
	                }
	            });
	        });
	        return isValid;
	    },
		});
		return NewBasicModel;
});
