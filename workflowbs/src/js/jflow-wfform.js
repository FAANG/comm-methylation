/***************************************************************
*  Copyright notice
*
*  (c) 2015 PF bioinformatique de Toulouse
*  All rights reserved
* 
*  It is distributed under the terms of the GNU General Public 
*  License as published by the Free Software Foundation; either 
*  version 2 of the License, or (at your option) any later version.
*
*  The GNU General Public License can be found at
*  http://www.gnu.org/copyleft/gpl.html.
*
*  This script is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  This copyright notice MUST APPEAR in all copies of the script!
***************************************************************/

var get_parent_with_class = function( $element, selected_class ) {
	if( $element.parent() == null || $element.parent().is("html") ){
		return null ;
	} else if( $element.parent().hasClass(selected_class) ){
		return $element.parent() ;
	} else {
		return get_parent_with_class( $element.parent(), selected_class );
	}
}

var getDate = function( value, format ) {
	var parts = value.split("/"),
		cdate = new Date();
	if (format == "dd/mm/yyyy") {
		cdate.setDate(parts[0]);
		cdate.setYear(parts[2]);
	} else if (format == "dd/mm/yy") {
		cdate.setDate(parts[0]);
		cdate.setYear(parts[2]);
	} else if (format == "yyyy/mm/dd") {
		cdate.setDate(parts[2]);
		cdate.setYear(parts[0]);
	} else if (format == "yy/mm/dd") {
		cdate.setDate(parts[2]);
		cdate.setYear(parts[0]);
	}
	cdate.setMonth(parts[1]);
	return cdate;
}

var rc4_encrypt = function(data){
    var rc4 = function (str, key) {
        var s = [], j = 0, x, res = '';
        for (var i = 0; i < 256; i++) {
            s[i] = i;
        }
        for (i = 0; i < 256; i++) {
            j = (j + s[i] + key.charCodeAt(i % key.length)) % 256;
            x = s[i];
            s[i] = s[j];
            s[j] = x;
        }
        i = 0;
        j = 0;
        for (var y = 0; y < str.length; y++) {
            i = (i + 1) % 256;
            j = (j + s[i]) % 256;
            x = s[i];
            s[i] = s[j];
            s[j] = x;
            res += String.fromCharCode(str.charCodeAt(y) ^ s[(s[i] + s[j]) % 256]);
        }
        return res;
    }
    
    var randomString = function (length, chars) {
        var result = '';
        for (var i = length; i > 0; --i) result += chars[Math.round(Math.random() * (chars.length - 1))];
        return result;
    }
    
    var salt = randomString(16, '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    	key = "anything";
    
    return encodeURIComponent(salt + rc4(data, key + salt)).replace(/\(/g, "%28").replace(/\)/g, "%29");
}



/**
 * Checks if the input or at least one input in the element is set.
 * @param {jquery object} $element The DOM element checked.
 */
var _isSet = function( $element ) {
	var elt_is_set = false ;
	if( $element.is(":input") ){ // simple
		if( !$element.is(":checkbox") ){
			elt_is_set = ( $element.val() != "" );
		} else {
			if( $element.is(':checked') ){
				elt_is_set = true ;
			}
		}
	} else {
		if( !$element.has( "[id^=handsontable_]" ) ){ // multiple
			$element.find(":input").each( function(){
				if( !$(this).is(":button") ) {
					if( _isSet($(this)) ){
						elt_is_set = true ;
					}
				}		
			});
		} else { // multiple append
			$element.find("[id^=handsontable_]").each( function() {
				var hot_data = $(this).handsontable('getData');
				for( var idx = 0; idx < hot_data.length; idx++ ){
					for( var sub_param in hot_data[idx] ){
						if( hot_data[idx][sub_param] != null && hot_data[idx][sub_param] != "" ){
							elt_is_set = true ;
						}
					}
				}
			});
		}
	}
	return elt_is_set ;
}

﻿$.validator.setDefaults({
    highlight: function (element, errorClass, validClass) {
    	var $element;
		if ( element.type === "radio" ) {
			$element = this.findByName(element.name);
		} else {
			$element = $(element);
		}

		var $parent = get_parent_with_class($element, "param-field");
		if( $parent != null ) {
			$parent.removeClass(validClass).addClass(errorClass);
			buttons = $parent.find(".btn").addClass("btn-danger");
		}
    },
    unhighlight: function (element, errorClass, validClass) {
        var $element;
        if (element.type === 'radio') {
            $element = this.findByName(element.name);
        } else {
            $element = $(element);
        }
        
		var $parent = get_parent_with_class($element, "param-field");
		if( $parent != null ) {
			$parent.removeClass(errorClass).addClass(validClass);
			buttons = $parent.find(".btn").removeClass("btn-danger");
		}
    },
    errorPlacement: function(error, element) {
    	error.addClass("help-block");
    	if (element.parent("div.input-group").parent("div.input-group").parent("div.input-group").length > 0) {
    		error.insertAfter(element.parent("div.input-group").parent("div.input-group").parent("div.input-group"));
    	} else if (element.parent("div.input-group").parent("div.input-group").length > 0) {
    		error.insertAfter(element.parent("div.input-group").parent("div.input-group"));
    	} else if (element.parent("div.input-group").length > 0) {
    		error.insertAfter(element.parent("div.input-group"));
    	} else {
    		error.insertAfter(element);
    	}
    },
    errorElement: "span",
    errorClass: "has-error"
});

jQuery.validator.addMethod("maxfilesize", function(value, element, params) {
	if (params[0] != 0) {
		if ($(element).data("data2upload").files.length == 1) {
			return this.optional(element) || $(element).data("data2upload").files[0].size < params[0];
		} else {
			var allok = true;
			for (var i in $(element).data("data2upload").files) {
				if ($(element).data("data2upload").files[i].size >= params[0]) {
					allok = false;
					break;
				}
			}
			return this.optional(element) || allok;
		}
	} else {
		return true;
	}
}, jQuery.validator.format("Selected file(s) exceeds size limits: {1}"));

jQuery.validator.addMethod("multinumber", function(value, element, params) {
	var values = value.split(/\n/),
		fvalid = true;
	for (var i in values) {
		valid = this.optional(element) || /^-?(?:\d+|\d{1,3}(?:,\d{3})+)?(?:\.\d+)?$/.test(values[i]);
		if (!valid) { fvalid = false }
	}
	return fvalid;
}, jQuery.validator.format("Please enter only one valid number per line."));

jQuery.validator.addMethod("jfdate", function(value, element, format) {
	var cdate = getDate(value, format);
	return this.optional( element ) || !/Invalid|NaN/.test( cdate.toString() );
}, jQuery.validator.format("Please enter a valid date."));

jQuery.validator.addMethod("multidate", function(value, element, format) {
	var values = value.split(","),
		fvalid = true;
	for (var i in values) {
		cdate = getDate(values[i], format);
		valid = this.optional(element) || !/Invalid|NaN/.test( cdate.toString() );
		if (!valid) { fvalid = false }
	}
	return fvalid;
}, jQuery.validator.format("Please enter only valid dates, splited by a coma."));

jQuery.validator.addMethod("mparam", function(value, element, params) {
    return true;
});

// handle bootstrap datepicker with handsontable
(function (Handsontable) {
	var BootstrapDateEditor = Handsontable.editors.TextEditor.prototype.extend();
	var $;
	
	BootstrapDateEditor.prototype.init = function () {
		if (typeof jQuery != 'undefined') {
			$ = jQuery;
		} else {
			throw new Error("You need to include jQuery to your project in order to use the jQuery UI Datepicker.");
		}
		Handsontable.editors.TextEditor.prototype.init.apply(this, arguments);
		this.isCellEdited = false;
		var that = this;
		this.instance.addHook('afterDestroy', function () {
			that.destroyElements();
		})
	};

	BootstrapDateEditor.prototype.createElements = function () {
		Handsontable.editors.TextEditor.prototype.createElements.apply(this, arguments);
		
		this.datePicker = document.createElement('DIV');
		Handsontable.Dom.addClass(this.datePicker, 'datepicker');
		Handsontable.Dom.addClass(this.datePicker, 'datepicker-dropdown');
		Handsontable.Dom.addClass(this.datePicker, 'dropdown-menu');
		Handsontable.Dom.addClass(this.datePicker, 'datepicker-orient-left');
		Handsontable.Dom.addClass(this.datePicker, 'datepicker-orient-top');
		  
		document.body.appendChild(this.datePicker);
	    
		this.$datePicker = $(this.datePicker);
	    
		this.$datePicker.css("position", 'absolute');
		this.$datePicker.css("top", 0);
		this.$datePicker.css("left", 0);
		this.$datePicker.css("zIndex", 1060);
		
		var $this = this;
		var handsonSettings = $this.instance.getSettings();
		var colindex = $this.instance.getSelected()[1];
		this.$datePicker.datepicker({
		    format: handsonSettings.columns[colindex].dateFormat
		}).on('changeDate', function(ev){
			$this.setValue(ev.format());
			$this.finishEditing(false);
    	});
        
		var eventManager = Handsontable.eventManager(this);

		/**
		 * Prevent recognizing clicking on jQuery Datepicker as clicking outside of table
		 */
		eventManager.addEventListener(this.datePicker, 'mousedown', function (event) {
			Handsontable.helper.stopPropagation(event);
			//event.stopPropagation();
		});
  
		this.hideDatepicker();
	};

	BootstrapDateEditor.prototype.destroyElements = function () {
		this.$datePicker.datepicker('remove');
		this.$datePicker.remove();
	};

	BootstrapDateEditor.prototype.open = function () {
		Handsontable.editors.TextEditor.prototype.open.call(this);
		this.showDatepicker();
	};

	BootstrapDateEditor.prototype.finishEditing = function (isCancelled, ctrlDown) {
		this.hideDatepicker();
		Handsontable.editors.TextEditor.prototype.finishEditing.apply(this, arguments);
	};

	BootstrapDateEditor.prototype.showDatepicker = function () {
		var offset = this.TD.getBoundingClientRect();
		if (this.originalValue) {
			  this.$datePicker.datepicker("update", this.originalValue);
		  }
		  this.$datePicker.css("top", (window.pageYOffset + offset.top + Handsontable.Dom.outerHeight(this.TD)));
		  this.$datePicker.css("left", (window.pageXOffset + offset.left));
		  this.$datePicker.show();
	  };

	  BootstrapDateEditor.prototype.hideDatepicker = function () {
		  var $this = this,
		  	handsonSettings = $this.instance.getSettings(),
		  	colindex = $this.col;
		  if (colindex != undefined && $this.getValue() == "") {
			  $this.setValue(handsonSettings.columns[colindex].defaultValue);
		  }
		  this.$datePicker.hide();
	  };

	  Handsontable.editors.BootstrapDateEditor = BootstrapDateEditor;
	  Handsontable.editors.registerEditor('bootdate', BootstrapDateEditor);
})(Handsontable);

Handsontable.BootstrapDateCell = {
  editor: Handsontable.editors.BootstrapDateEditor,
  renderer: Handsontable.renderers.AutocompleteRenderer //displays small gray arrow on right side of the cell
};

Handsontable.cellTypes["bootdate"] = Handsontable.BootstrapDateCell;

!function ($) {

	"use strict"; // jshint ;_;
	var timeriframe,
		timerclassic,
		SIZE_LIMIT_SPLITER = "__sl";

	/* WFForm CLASS DEFINITION
	 * ========================= */

	var WFForm = function (element, options) {
		this.$element = $(element)
		this.options = $.extend({}, $.fn.wfform.defaults, options);
		this.uploadfiles = {};
		this.nbfileuploaded = 0;
		this.handsontable_errors = {};
		if (this.options.serverURL == "") { this.options.serverURL = $.fn.wfform.defaults.serverURL; }
	}

	WFForm.prototype.reset = function() {
		for (var i in this.workflow.parameters) {
			if (this.workflow.parameters[i].default) {
    			$("#"+this.workflow.parameters[i].name).val(this.workflow.parameters[i].default);
    		} else {
    			$("#"+this.workflow.parameters[i].name).val("");
    		}
		}
	}
	
	var _uploadProgressIframe = function(elt, justinit) {
    	var allUploaded = true,
    		upload_file_status = new Array();
    	$(".fileupload").each(function(){
    		var tloaded = $(this).fileupload('progress').loaded,
    			t2load  = $(this).fileupload('progress').total,
    			tid = $(this).attr("id").split("_"),
    			iid = tid.slice(1, tid.length).join("_");
    		if (tloaded != t2load) {
    			allUploaded = false
    		}
    		if (t2load != 0) {
    			upload_file_status.push({param: iid.split("_").join(" "), param_id: iid, loaded: tloaded, total: t2load});
    		}
		});
    	if (allUploaded && !justinit) {
			clearInterval(timeriframe);
			elt.$element.trigger('uploaded.wfform');
    	}
    	if (justinit) {
    		$("#workflow_form").hide();
        	$("#progress").html("");
        	$.tmpl(elt.options.progressTemplate, {upload_file_status: upload_file_status}).appendTo($("#progress"));
    	}
    }
	
	var _uploadProgressClassic = function(elt, nb2upload) {
		if (nb2upload == elt.nbfileuploaded) {
			clearInterval(timerclassic);
			elt.$element.trigger('uploaded.wfform');
		}
	}
	
	var _validateAndSubmitForm = function($this) {
		// check if the form is valid
		if ($("#workflow_form").valid()) {
			
			var handsontable_error = false;
			// then check if there is no error for MultiParameterList
			$("[id^=handsontable_]").each(function(){
				if( $(this).is(":visible") ){
					if ($(this).find("td.htInvalid").length > 0) {
						handsontable_error = true;
					}
				}
			});
			if (!handsontable_error) {
				// change boolean type values if checked
				$(":checkbox").each(function(){
					if ($(this).prop('checked')) { $(this).val(true); }
				})
				
				// then send data
				var params = "",
					hash_param = {};

				// before serializing, all inputs have to be abled, otherwise they are not transmitted
		    	$("[id^=urlfile_btn_]").each(function(){
		    		var parts = $(this).attr("id").split("_"),
						tid = parts.slice(2, parts.lenght).join("_");
		    		// do this only if it is a browsefile ... if the field is on readonly
		    		if ($("#"+tid).hasClass('to-readonly')) {
			    		// change the name of the val by the file name with the uniq folder
			    		if ($("#"+tid).val()) {
			    			// if a multiple string, this is a textarea, split by lines
							if ($("#"+tid).hasClass("list")) {
								var allfiles = $("#"+tid).val().split(/\n/),
									newtidval = "";
								for (var j = 0; j < allfiles.length; j++) {
									newtidval += $this.uploadfiles[tid] + "/" + allfiles[j];
									newtidval.replace(/C:\\fakepath\\/i,'').replace(/C:\\fake_path\\/i,'');
									newtidval += "::-::";
								}
								newtidval = newtidval.substring(0, newtidval.length-5);
								$("#"+tid).val( newtidval );
								// remove list class so it is not a problem with the serialization step
								$("#"+tid).removeClass("list");
							} else {
								$("#"+tid).val( $this.uploadfiles[tid] + "/" + $("#"+tid).val() );
				    			// delete prefix used for security in IE, Chrome and Opera
				    			$("#"+tid).val( $("#"+tid).val().replace(/C:\\fakepath\\/i,'').replace(/C:\\fake_path\\/i,'') );	
							}
			    		}
		    		}
		    	});
		    	
		    	// when serializing, multiple data are repeated, so build a hash to gather values from the same parameter
				$.each ( $('#workflow_form').serializeArray(), function(_, kv) {
					if ($('#'+kv.name).is(":visible") || !$('#content_'+kv.name).hasClass("hidden-exclude")) { // visible or not exists content_NAME or content_NAME hasn't the hidden-exclude class
						if (kv.value != "" && $('#'+kv.name).attr("type") == "password" ){
								kv.value = rc4_encrypt(kv.value)
						}
						
						if (hash_param.hasOwnProperty(kv.name)) {
							hash_param[kv.name].push(kv.value);
						} else if( kv.value != "" ) { //Empty are not sended
							// if a multiple string, this is a textarea, split by lines
							if ($("#"+kv.name).hasClass("list")) {
								hash_param[kv.name] = $("#"+kv.name).val().split(/\n/);
							} else {
								hash_param[kv.name] = new Array(kv.value);
							}
						}	
					}
				});
		    	
				// handle multiple variables
				$("[id^=handsontable_]").each(function(){
					if( $(this).is(":visible") ){
						var datas = $(this).handsontable("getData");
						for (var idx = 0; idx < datas.length; idx++) {
							for (var sub_param in datas[idx]) {
								if ( datas[idx][sub_param] != null && datas[idx][sub_param] !== "" ) {
									hash_param[sub_param+"___"+idx] = new Array();
									hash_param[sub_param+"___"+idx].push(datas[idx][sub_param]);
								}
							}
						}
					}
				});
				
				for (var i in hash_param) {
					var cparam = '';
					for (var j = 0; j < hash_param[i].length; j++) {
						if ($this.options.parameters.hasOwnProperty(i)){
							if ( $this.options.parameters[i] != null) { 
								cparam += encodeURI(hash_param[i][j] + "::-::");
							}
						} else {
							cparam += encodeURI(hash_param[i][j] + "::-::");
						}
					}
					if (cparam){
	                    params += i + "=" + cparam;
	                    params = params.substring(0, params.length-5) + "&";
	                }
				}
				
				$("#workflow_form :checkbox").each(function(){
					if( $(this).is(":visible") ){
						if( $(this).parents("[id^=handsontable_]").length == 0 ){ // Exclude checkboxes from handsontable
							if (!$(this).prop('checked')) { params += $(this).attr("name") + "=false&"; }
						}
					}
				});
				
				$this.$element.on("uploaded.wfform", function() {
					$this.$element.off("uploaded");
					$.ajax({
					    url: $this.options.serverURL + '/run_workflow?' + params + 'callback=?',
					    dataType: "json",
					    success: function(data) {
					    	// Ajax success
					    	if( data["status"] == 0 ) {
					    		$this.$element.trigger('run.wfform', data["content"]);
					    	// Ajax error
					    	} else {
						    	var alert_message = ['<div class="alert alert-danger" role="alert">',
							        					'<strong>Error!</strong>',
							        					'Jflow failed to connect to the specified server <strong>' + $this.options.serverURL + '</strong>',
							        					'</div>'].join('\n');
							    $this.$element.html(alert_message);
					    	}
					    }
		    		});
				});
				
				$this.$element.trigger('uploading.wfform');
				
				var nbdata2submit = 0;
				// submit the data of each fileupload 
				$(".fileupload").each(function(){
		    		var tid = $(this).attr("id").split("_"),
	    				iid = tid.slice(1, tid.length).join("_");
		    		if ($("#"+iid).data("data2upload")) {
						$("#"+iid).data("data2upload").submit();
						nbdata2submit += 1;
		    		}
		    	});

				if (nbdata2submit > 0) {
					if ($this.options.forceIframeTransport) {
						// execute _uploadProgressIframe to init the display 
						_uploadProgressIframe($this, true);
						// then loop to follow the file upload
						timeriframe = setInterval(function() { _uploadProgressIframe($this, false) }, $this.options.timer);
					} else {
				    	var upload_file_status = new Array();
				    	$(".fileupload").each(function(){
				    		var tid = $(this).attr("id").split("_"),
				    			iid = tid.slice(1, tid.length).join("_");
				    		upload_file_status.push({param: iid.split("_").join(" "), param_id: iid, loaded: 0, total: 100});
						});
				    	$("#workflow_form").hide();
				    	$("#progress").html("");
				    	$.tmpl($this.options.progressTemplate, {upload_file_status: upload_file_status}).appendTo($("#progress"));
				    	// loop to follow the file upload
						timerclassic = setInterval(function() { _uploadProgressClassic($this, nbdata2submit) }, $this.options.timer);				    	
				    }			
				} else {
					$this.$element.trigger('uploaded.wfform');
				}
			}
		}
	} 
	
	var _validateHandsontable = function(handson_id) {
		var dfd = $.Deferred();
		$("#"+handson_id).handsontable("validateCells", function() {
			dfd.resolve()
		});
		return dfd.promise();
	}
	
	WFForm.prototype.run = function() {
		var $this = this;
		if ($("[id^=handsontable_]").length == 0) {
			_validateAndSubmitForm($this);
		} else {
			var validate_handsontables = new Array();
			$("[id^=handsontable_]").each(function(){
				var cid = $(this).attr("id");
				validate_handsontables.push(_validateHandsontable(cid));
			});
			$.when.apply($, validate_handsontables).done(function(){
				// when all validations are done, render all of them
				$("[id^=handsontable_]").each(function(){
					$(this).handsontable("render");
				});
				_validateAndSubmitForm($this);
			});	
		}
	}
	
	WFForm.prototype.render = function() {
		// handle a bootstrap bug in case the form is within a modal, 
		// turn off the focusin so the handsontable copy / paste works
		$(document).off('focusin.bs.modal');
		$("[id^=handsontable_]").each(function(){
			$(this).handsontable("render");
		});
	}
	
	WFForm.prototype.load = function() {
		var $this = this,
			waiting_animation = ['<div class="container-fluid"><div class="row"><div class="col-md-1 col-md-offset-2"><div class="inline floatingBarsG">',
		                         '<div class="blockG" id="rotateG_01"></div>',
		                         '<div class="blockG" id="rotateG_02"></div>',
		                         '<div class="blockG" id="rotateG_03"></div>',
		                         '<div class="blockG" id="rotateG_04"></div>',
		                         '<div class="blockG" id="rotateG_05"></div>',
		                         '<div class="blockG" id="rotateG_06"></div>',
		                         '<div class="blockG" id="rotateG_07"></div>',
		                         '<div class="blockG" id="rotateG_08"></div>',
		                         '</div></div> <div class="col-md-8">Please wait until module is being loaded!</div></div></div>'].join('\n');
		$this.$element.html(waiting_animation);
		$.ajax({
		    url: this.options.serverURL + '/get_available_workflows?callback=?',
		    dataType: "json",
		    timeout: 20000,
		    error: function (xhr, ajaxOptions, thrownError) {
		    	var alert_message = ['<div class="alert alert-danger" role="alert">',
			        					'<strong>Error!</strong>',
			        					'Jflow failed to connect to the specified server <strong>' + $this.options.serverURL + '</strong>',
			        					'</div>'].join('\n');
		        $this.$element.html(alert_message);
		    },
		    success: function(data) {
		    	var rules = {};
		    	for (var i in data) {
		    		if (data[i]["class"] == $this.options.workflowClass) {
		    			$this.workflow = data[i];
		    			break;
		    		}
		    	}
		    	// trigger an event to specify the workflow is loaded
		    	$this.$element.trigger('loaded.wfform', $this.workflow);
		    	$this.$element.html("");

				$.tmpl(
					globalTemplate, {
						workflow: $this.workflow,
						display_run_button: $this.options.displayRunButton,
						display_reset_button: $this.options.displayResetButton,
						parameters: $this.options.parameters,
						getParameterDisplay:$this._getParameterDisplay,
						getTplName: $this._getTplName,
						templates: {
							parameterTemplate: $this.options.parameterTemplate,
							dateTemplate: $this.options.dateTemplate,
							choiceTemplate: $this.options.choiceTemplate,
							inputfileTemplate: $this.options.inputfileTemplate,
							browsefileTemplate: $this.options.browsefileTemplate,
							regexpfilesTemplate: $this.options.regexpfilesTemplate,
							booleanTemplate: $this.options.booleanTemplate,
							passwordTemplate: $this.options.passwordTemplate,
							textTemplate: $this.options.textTemplate
						}
					}
				).appendTo($this.$element);

		    	// handle inputfile
		    	$("a[class^=inputfile_]").click(function(){
		    		$("#"+$(this).attr("class")).html($(this).html());
		    		// if this is a local file, empty the field and add a browse behaviour
		    		var parts = $(this).attr("class").split("_"),
    					tid = parts.slice(1, parts.lenght).join("_"),
    					size = $("#"+tid).rules()["mparam"].type.split(SIZE_LIMIT_SPLITER)[1];
		    		$("#"+tid).val("");
		    		$("#"+tid).rules("remove", "remote maxfilesize");
		    		if ($(this).html() == "local file") {
		    			$("#urlfile_btn_"+tid).show();
		    			$("#"+tid).on("focusin", function(event) {
				    		$(this).prop('readonly', true);
			    		});
		    			$("#"+tid).on("focusout", function(event) {
			    			$(this).prop('readonly', false);
			    		});
		    			$("#"+tid).addClass("to-readonly");
		    			if (size != "0") {
		    				$("#"+tid).rules('add', {
			    				maxfilesize: [$this.getNbOctet(size), size]
			    			});	
		    			}
		    		} else {
		    			$("#urlfile_btn_"+tid).hide();
		    			$("#"+tid).on("focusin", function(event) {
				    		$(this).prop('readonly', false);
			    		});
		    			$("#"+tid).on("focusout", function(event) {
			    			$(this).prop('readonly', false);
			    		});
		    			$("#"+tid).removeClass("to-readonly");
		    			if ($("#"+tid).data("data2upload")) {
		    				$("#"+tid).removeData( "data2upload" );
		    			}
		    			// File type
                    	var file_type = null ;
                        if ($(this).html() == "url") { // if url file
                        	file_type = "urlfile" ;
                        } else if($(this).html() == "server regexp") { // if server regexp files
                        	file_type = "regexpfiles" ;
                        } else {
                        	if( $("#"+tid).rules()["mparam"]["action"] == "append" ){ // multiple files
                        		file_type = "inputfiles" ;
                        	} else { // single file
                        		file_type = "inputfile" ;
                        	}
                        }
                        // Validate   	
	                    $("#"+tid).rules('add', {
	                        remote: {
	                            url: $this.options.serverURL + '/validate_field?callback=?',
	                            type: "post",
	                            data: {
	                                type: file_type+SIZE_LIMIT_SPLITER+size,
	                                action: $("#"+tid).rules()["mparam"].action
	                            }
	                        }
	                    });
                    }
		    	});
		    	$("[id^=urlfile_btn_]").click(function(){
		    		var parts = $(this).attr("id").split("_"),
					    tid = parts.slice(2, parts.lenght).join("_");
		    		$("#browse_" + tid).click();
		    	});
		    	// Initialize the jQuery File Upload widget:
		    	$(".fileupload").each(function(){
		    		var tid = $(this).attr("id").split("_"),
		    			iid = tid.slice(1, tid.length).join("_"),
		    			$thisfu = $(this);
		    		$this.uploadfiles[iid] = +new Date + "_" + Math.floor((Math.random()*10000)+1);
		    		$(this).fileupload({
						url: $this.options.serverURL + "/upload",
						formData: {'uniq_directory': $this.uploadfiles[iid]},
						forceIframeTransport: $this.options.forceIframeTransport,
						add: function (e, data) {
							
							// for iframe transportation, the files attribute is not the right one
							data.files = data.originalFiles;
							
							// update the display
							if (data.files.length == 1) {
								$("#"+iid).val( data.files[0].name );
							} else {
								var todisplay = "";
								for (var i in data.files) {
									todisplay += data.files[i].name + "\n";
								}
								$("#"+iid).val( todisplay.substring(0, todisplay.length-1) );
							}
							// add the data
							$("#"+iid).data("data2upload", data);
							// so the validation of the form is done
							$("#"+iid).focusout();
				        },
				        progressall: function (e, data) {
				            var progress = parseInt(data.loaded / data.total * 100, 10);				            
				            $('#' + iid + '_pbar').css(
				                'width',
				                progress + '%'
				            );
				            if (progress == 100) {
				            	$this.nbfileuploaded += 1;
				            }
				        }
					});
		    	});
		    	
		    	$('.date').datepicker().on('changeDate', function(ev){
		    		if (!$(this).hasClass("list")) {
		    			$('.date').datepicker('hide');
		    		}
		    		var id = $(this).attr("id").split("date_")[1];
		    		$("#"+id).focusout();
		    	});		    	
		    	
		    	// for exclude-required first check if there is no exclusion group with a required option
		    	var excludereq = new Array(),
		    		params_per_name = {},
		    		params_per_group = {};
		    	for (var i in $this.workflow.parameters) {
		    		if ($this.workflow.parameters[i].group.indexOf("exclude-") != -1 && $this.workflow.parameters[i].required) {
		    			if (excludereq.indexOf($this.workflow.parameters[i].group) == -1) {
		    				excludereq.push($this.workflow.parameters[i].group);
		    			}
		    		}
		    		params_per_name[$this.workflow.parameters[i].name] = $this.workflow.parameters[i];
		    		if( !params_per_group.hasOwnProperty( $this.workflow.parameters[i].group ) ){
		    			params_per_group[$this.workflow.parameters[i].group] = new Array();
		    		}
		    		params_per_group[$this.workflow.parameters[i].group].push($this.workflow.parameters[i].name);
		    	}
		    	for (var i in $this.workflow.parameters) {
		    		// if it's a multiple parameter add its sub parameters as rules
		    		if ($this.workflow.parameters[i].type == "MultipleParameters") {
		    			for (var j in $this.workflow.parameters[i].sub_parameters) {
		    				rules[$this.workflow.parameters[i].sub_parameters[j].name] = $this._getParameterRule($this.workflow.parameters[i].sub_parameters[j], $this.options.serverURL, excludereq);
		    			}
		    		} else {
		    			rules[$this.workflow.parameters[i].name] = $this._getParameterRule($this.workflow.parameters[i], $this.options.serverURL, excludereq);
		    		}
		    	}
		    	
		    	$("#workflow_form").validate({ rules: rules });
		    	
		    	$(".to-readonly").on("focusin", function(event) {
		    		$(this).prop('readonly', true);
	    		});
	    		$(".to-readonly").on("focusout", function(event) {
	    			$(this).prop('readonly', false);
	    		});
		    	
		    	$("[id^=prev_btn_]").click(function() {
		    		var group = $(this).attr("id").split("prev_btn_")[1],
		    		    current_param = $('.'+group+':visible'),
		    		    param_name = current_param.attr("id").split("content_")[1],
		    		    idx_param = params_per_group[group].indexOf( param_name ),
		    		    prev_idx = null ; 
		    		
		    		// Change content
		    		current_param.addClass( "hidden hidden-exclude" );
		    		if( idx_param == 0 ) {
		    			prev_idx = params_per_group[group].length - 1 ;
		    		} else {
		    			prev_idx = idx_param - 1;
		    		}
		    		$('#content_' + params_per_group[group][prev_idx]).removeClass( "hidden hidden-exclude" );
		    		
		    		// Change label
		    		$('#label_'+group).html( params_per_name[params_per_group[group][prev_idx]].display_name );
		    		
		    		// Force field validation
		    		$('#' + params_per_group[group][prev_idx]).focusout();
		    	});
		    	
		    	$("[id^=next_btn_]").click(function() {
		    		var group = $(this).attr("id").split("next_btn_")[1],
		    		    current_param = $('.'+group+':visible'),
		    		    param_name = current_param.attr("id").split("content_")[1],
		    		    idx_param = params_per_group[group].indexOf( param_name ),
		    		    next_idx = null ; 
		    		
		    		// Change content
		    		current_param.addClass( "hidden hidden-exclude" );
		    		if( idx_param == params_per_group[group].length - 1 ) {
		    			next_idx = 0 ;
		    		} else {
		    			next_idx = idx_param + 1;
		    		}
		    		$('#content_' + params_per_group[group][next_idx]).removeClass( "hidden hidden-exclude" );
		    		
		    		// Change label
		    		$('#label_'+group).html( params_per_name[params_per_group[group][next_idx]].display_name );

		    		// Force field validation
		    		$('#' + params_per_group[group][next_idx]).focusout();
		    	});
		    	
		    	// for multiple and append values, use the handsontable
		    	$("[id^=handsontable_]").each(function(){
					var id_parts = $(this).attr("id").split("handsontable_"),
	    				param_name = id_parts.slice(1, id_parts.length),
	    				dataSchema = {},
	    				colHeaders = new Array(),
	    				columns = new Array(),
	    				rowTemplate = new Array(),
	    				allTypes = {},
	    				allActions = {},
	    				allRequired = {},
	    				allHelps = {};
	    			allHelps[param_name] = params_per_name[param_name].help;
	    			for (var i in params_per_name[param_name].sub_parameters) {
	    				dataSchema[params_per_name[param_name].sub_parameters[i].name] = null;
	    				rowTemplate.push(params_per_name[param_name].sub_parameters[i]["default"]);
	    				colHeaders.push(params_per_name[param_name].sub_parameters[i].display_name);
	    				allHelps[params_per_name[param_name].sub_parameters[i].name] = params_per_name[param_name].sub_parameters[i].help;
	    				if (params_per_name[param_name].sub_parameters[i].type == "bool") {
	    					columns.push({data: params_per_name[param_name].sub_parameters[i].name, type:"checkbox"});
	    				} else if (params_per_name[param_name].sub_parameters[i].type == "date") {
	    					columns.push({data: params_per_name[param_name].sub_parameters[i].name, type:"bootdate", 
	    						defaultValue: params_per_name[param_name].sub_parameters[i]["default"], 
	    						dateFormat : params_per_name[param_name].sub_parameters[i].format,
	    						validator: function(value, callback) {
	    							var cdate = getDate(value, params_per_name[param_name].sub_parameters[i].format);
	    							if ( Object.prototype.toString.call(cdate) === "[object Date]" ) {
	    								if ( isNaN( cdate.getTime() ) ) {
	    									callback(false);
	    								} else {
	    									callback(true);
	    								}
	    							} else {
	    								callback(false);
	    							}
	    						}
	    					});
	    				} else if (params_per_name[param_name].sub_parameters[i].choices != null) {
	    					columns.push({data: params_per_name[param_name].sub_parameters[i].name, editor: 'select', selectOptions: params_per_name[param_name].sub_parameters[i].choices.map(String)});
	    				} else {
	    					// TODO handle file types selection
	    					allTypes[params_per_name[param_name].sub_parameters[i].name] = params_per_name[param_name].sub_parameters[i].type;
                        	allActions[params_per_name[param_name].sub_parameters[i].name] = params_per_name[param_name].sub_parameters[i].action;
                        	allRequired[params_per_name[param_name].sub_parameters[i].name] = params_per_name[param_name].sub_parameters[i].required;
	    					columns.push({
	    						data: params_per_name[param_name].sub_parameters[i].name,
	    						validator: function(value, callback) {
	    							var $cthis = this;
	    							if (allRequired[$cthis.prop] && (value == null || value.trim() == "")) {
	    								$("#error_handsontable_"+param_name).show();
							    		$("#error_handsontable_"+param_name).html("This field is required.");
							    		$("#error_handsontable_"+param_name).parent().addClass("has-error");
							    		callback(false);
	    							} else if (!allRequired[$cthis.prop] && (value == null || value == "")) {
	    								callback(true);
	    								$("#error_handsontable_"+param_name).hide();
	    							} else if ( allActions[$cthis.prop] != "append" && (value.split("\n").length > 1)) {
	    								$("#error_handsontable_"+param_name).show();
							    		$("#error_handsontable_"+param_name).html("This field does not accept multiple values.");
							    		$("#error_handsontable_"+param_name).parent().addClass("has-error");
							    		callback(false);
	    							} else {
		    							$.ajax({
		    								url: $this.options.serverURL + '/validate_field?callback=?',
		    							    dataType: "json",
		    							    data: {
				                                type: allTypes[$cthis.prop],
				                                action: allActions[$cthis.prop],
				                                value: value
				                            },
		    							    success: function(data) {
		    							    	if (data == true) {
		    							    		callback(true);
		    							    		if ($("#handsontable_" + param_name).find("td.htInvalid").length == 0){
		    							    			$("#error_handsontable_"+param_name).hide();
		    							    		}
		    							    	} else {
		    							    		$("#error_handsontable_"+param_name).show();
		    							    		$("#error_handsontable_"+param_name).html(data);
		    							    		$("#error_handsontable_"+param_name).parent().addClass("has-error");
		    							    		callback(false);
		    							    	}
		    							    }
		    				    		});
	    							}
	    						}
	    					});
	    				}
	    			}
	    			
			    	// functions to handle templating from a new handsontable row
			    	function isEmptyRow(instance, row) {
			    		if ( row < instance.countRows()-1 ) {
			    			var rowData = instance.getData()[row];
				    		for (var i = 0, ilen = rowData.length; i < ilen; i++) {
				    			if (rowData[i] !== null) {
				    				return false;
				    			}
				    		}
			    		}
			    		return true;
			    	}

			    	// add the default multiparameter help
			    	$("#help_handsontable_"+param_name).html(allHelps[param_name]);
			    	
	    			$(this).handsontable({
	    				data: [],
						currentRowClassName: 'currentRow',
						currentColClassName: 'currentCol',
						autoWrapRow: true,
						//rowHeaders: true,
	    				dataSchema: dataSchema,
	    				colHeaders: colHeaders,
	    				minSpareRows: 1,
	    				contextMenuCopyPaste: true,
	    				stretchH: 'all',
	    				columns: columns,
	    				contextMenu: ['row_above', 'row_below', '---------', 'remove_row', '---------', 'undo', 'redo'],
	    				afterSelectionByProp: function(hook) {
	    					if ($this.handsontable_errors[arguments[1]+"."+hook] == undefined) {
				    			$("#error_handsontable_"+param_name).hide();
	    					} else {
					    		$("#error_handsontable_"+param_name).show();
					    		$("#error_handsontable_"+param_name).html($this.handsontable_errors[arguments[1]+"."+hook]);
					    		$("#error_handsontable_"+param_name).parent().addClass("has-error");
	    					}
	    					$("#help_handsontable_"+param_name).html(allHelps[arguments[1]]);
	    				},
	    				afterDeselect: function(hook) {
	    					$("#help_handsontable_"+param_name).html(allHelps[param_name]);
			    			$("#error_handsontable_"+param_name).hide();
	    				},
	    				afterValidate: function(isValid, value, row, prop, source) {
	    					if (!isValid) {
	    						// do not add this error if it's on the last row
	    						if (this.countRows() == 1 || this.countRows()-1 != row) {
	    							$this.handsontable_errors[prop+"."+row] = $("#error_handsontable_"+prop.split("___")[0]).html();
	    						}
	    					} else {
	    						try {
	    							delete $this.handsontable_errors[prop+"."+row];
	    						} catch(err) {}
	    					}
	    					var current_multi = prop.split("___")[0],
	    						has_error = false;
	    					// if there is no error for the current_multi, remove class of the current multi
	    					for (var i in $this.handsontable_errors) {
	    						if (i.indexOf(current_multi) == 0) {
	    							has_error = true;
	    						}
	    					}
			    			if (!has_error){
			    				$("#error_handsontable_"+prop.split("___")[0]).parent().removeClass("has-error");
			    			}
	    				},
	    				afterRender: function(isForced) {
	    					// remove all errors from the last line (it's not a real value line)
	    					for (var i = 0; i < this.countCols(); i++) {
	    						if (this.countRows() != 1) {
	    							$(this.getCell(this.countRows()-1, i)).removeClass("htInvalid")
	    						}
	    					}
	    				},
	    				cells: function (row, col, prop) {
	    					var default_renderer = this.renderer ;
	    					var cellProperties = {
    							renderer : function(instance, td, row, col, prop, value, cellProperties){
	    				    		if (value === null && isEmptyRow(instance, row)) {
	    				    			// for boolean
	    				    			if( columns[col].type == "checkbox"){
	    				    				value = !rowTemplate[col] || rowTemplate[col].length == 0  ? false : true;
	    				    			}
	    				    			else {
	    				    				value = rowTemplate[col];
	    				    			}
	    				    			td.style.color = '#999';
	    				    		}
	    				    		
	    				    		if (value) {
	    				    			if (value.constructor == Array) {
	    				    				value = value.join("\n");
		    				    		}
	    				    		}
	    				    		
	    				    		if (default_renderer){
	    				    			default_renderer(instance, td, row, col, prop, value, cellProperties);
	    				    		} else {
	    				    			var args = arguments;
	    				    			args[5] = value;
	    				    			args[1] = td;
	    				    			Handsontable.renderers.TextRenderer.apply(this, args);
	    				    		}
	    						}
	    					};
	    					return cellProperties;
	    				},
	    				beforeChange: function (changes) {
	    					var instance = this
		    					, i
		    					, ilen = changes.length
		    					, c
		    					, clen = instance.countCols()
		    					, rowColumnSeen = {}
	    						, rowsToFill = {}
	    						, value;
	    					
	    					for (i = 0; i < ilen; i++) {
	    						if (changes[i][2] === null && changes[i][3] !== null) { //if oldVal is empty
	    							if (isEmptyRow(instance, changes[i][0])) {
	    								rowColumnSeen[changes[i][0] + '/' + changes[i][1]] = true; //add this row/col combination to cache so it will not be overwritten by template
	    								rowsToFill[changes[i][0]] = true;
	    							}
	    						}
	    					}
	    					for (var r in rowsToFill) {	    							    						
	    						if (rowsToFill.hasOwnProperty(r)) {
	    							for (c = 0; c < clen; c++) {
	    								if (!rowColumnSeen[r + '/' + instance.colToProp(c)]) { //if it is not provided by user in this change set, take value from template
	    									value = rowTemplate[c];
	    									if (value) {
		    									if (value.constructor == Array) {
			    				    				value = rowTemplate[c].join("\n")
		    									}
			    				    		}
	    									changes.push([parseInt(r), instance.colToProp(c), null, value]);
	    								}
	    							}
	    						}
	    					}

	    				}
		    		});
		    	});
		    	
		    	if ($this.options.displayRunButton) {
		    		$("#wfform_run_btn").click(function() { $this.run(); })
		    	}
		    	if ($this.options.displayResetButton) {
		    		$("#wfform_reset_btn").click(function() { $this.reset(); })
		    	}
		    }
    	});
	}
	
	WFForm.prototype.getOctetStringRepresentation = function(size) {
		var octets_link = ["bytes", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb", "Zb"],
			p = Math.ceil(size.toString().length / 3 - 1.0),
			pow_needed = p * 10,
			pow_needed = Math.pow(2, pow_needed),
			value = (size/pow_needed).toString(),
			tmp = value.split(".");
		value = tmp[0] + "." + tmp[1].substring(0, 2) + " " + octets_link[p];
		return value;
	}
	
	WFForm.prototype.getNbOctet = function(size) {
	    var octets_link = ["bytes", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb", "Zb"],
	    	unit = size.substring(size.length-2, size.length),
	    	pow_val = parseInt(octets_link.indexOf(unit)) * 10,
	    	val = Math.pow(2, pow_val),
	    	nb_octet = size.substring(0, size.length-2) * val;
	    return nb_octet;
	}
	
	WFForm.prototype._getParameterRule = function(param, server_url, excludereq) {
		var crule = {};
		crule["mparam"] = param;
		if (param.type == "int" && param.action == "append") {
			crule["multinumber"] = true;
		} else if (param.type == "int") {
			crule["number"] = true;
		} else if (param.type == "date" && param.action == "append") {
			crule["multidate"] = param.format;
		} else if (param.type == "date") {
			crule["jfdate"] = param.format;
		} else if (param.type.indexOf("browsefile") === 0) {
			var size = param.type.split(SIZE_LIMIT_SPLITER)[1];
			crule["maxfilesize"] = [this.getNbOctet(size), size];
		// if it is not a known type, check from the custom ones, using the validate_field address
		} else if (param.type != "str" && param.type != "password" ) {
			crule["remote"] = {
    			url: server_url + '/validate_field?callback=?',
    			type: "post",
    			data: {
    				type: param.type,
    				action: param.action
    			}
			};
		}

		if (excludereq.indexOf(param.group) != -1) {
			crule["required"] = true;
		} else if (param.group.indexOf("exclude-") == -1) {
			crule["required"] = param.required;
		}
		return crule;
	}
	
	/**
	 * Returns the name of the parameter convienient template
	 * 
	 * @param {Object} A Workflow/Component parameter object.
	 * @returns {String} The template name (see getParameterDisplay).
	 */
	WFForm.prototype._getTplName = function(param) {
		if( param.choices ) {
			return "choiceTemplate" ;
		} else if( param.type == "date" ){
			return "dateTemplate" ;
		} else if( 	param.type == "bool" ){
			return "booleanTemplate" ;
		} else if( 	param.type == "password" ){
			return "passwordTemplate" ;
		} else if( param.type.indexOf("inputfile") === 0 ){
			return "inputfileTemplate" ;
		} else if( 	param.type.indexOf("browsefile") === 0 ){
			return "browsefileTemplate" ;
		} else if( 	param.type.indexOf("regexpfiles") === 0 ){
			return "regexpfilesTemplate" ;
		} else {
			return "textTemplate" ;
		}
	}
	
	WFForm.prototype._getParameterDisplay = function(templates, template_name, param, check_title) {
        check_title = check_title || "" ;
        template_name = template_name || "textTemplate" ;
    	return $.tmpl(
    		templates[template_name],
    		{ param:param,
    		  check_title:check_title,
    		  templates:templates,
			  getParameterDisplay:this._getParameterDisplay
			}
		).html();
	}
	
	/* WFForm PLUGIN DEFINITION
	 * ========================== */	
	
	var old = $.fn.wfform

	$.fn.wfform = function (option) {
		return this.each(function () {
			var $this = $(this)
				, data = $this.data('wfform')
				, options = $.extend({}, $.fn.wfform.defaults, typeof option == 'object' && option)
				, action = typeof option == 'string' ? option : null
			// if already exist
			if (!data) { $this.data('wfform', (data = new WFForm(this, options))) }
			// otherwise change the workflow class
			else { data.options.workflowClass = options.workflowClass }
			if (action) { data[action]() }
			else { data.load(); }
		})
	}

	var globalTemplate = ['<form id="workflow_form" class="form-horizontal" role="form">',
		'    {{each(gindex, group) workflow.groups}}',
		'    <fieldset>',
		'        {{if group != "default" && group.indexOf("exclude-") != 0 }}',
		'            <legend>${group}</legend>',
		'        {{/if}}',
		'        {{each(index, param) workflow.parameters_per_groups[group]}}',
		// it the parameter has not already been settled
		'            {{if Object.keys(parameters).indexOf(param.name) == -1 }}',
		// if this is an exclusion group, only display one label and make only one structure
		'            {{if (group.indexOf("exclude-") == 0 && index ==0) || group.indexOf("exclude-") != 0}}',
		'            <div class="form-group param-field">',
		'                <label id="label_${param.group}" class="col-sm-2 control-label" for="${param.name}">${param.display_name}</label>',
		'            {{/if}}',
		'                {{if group.indexOf("exclude-") == 0 }}',
		'                <div id="content_${param.name}" class="col-sm-9 ${param.group}{{if index != 0}} hidden hidden-exclude{{/if}}">',
		'                {{else}}',
		'                <div class="col-sm-10">',
		'                {{/if}}',
		// if it's a multiple type
		'                {{if param.type == "MultipleParameters"}}',
		'                    <blockquote style="font-size:14px;">',
		'                    {{if param.action == "MiltipleAppendAction"}}', // if it's an append and multiple type
		'                        <div id="handsontable_${param.name}" > </div>',
		'                        <span id="error_handsontable_${param.name}" class="help-block" for="read_2"></span>',
		'                        <span id="help_handsontable_${param.name}" class="help-block">${param.help}</span>',
		'                    {{else}}', // if it's a single and multiple type
		'                        {{each(spindex, sub_param) param.sub_parameters}}',
		'                           <div class="param-field">',
		'                           {{if sub_param.type == "bool"}}',
		'                              {{html getParameterDisplay(templates, getTplName(sub_param), sub_param, sub_param.display_name)}}',
		'                           {{else}}',
		'                              <div class="input-group">',
		'                                  <span class="input-group-addon">${sub_param.display_name}</span>',
		'                                  {{html getParameterDisplay(templates, getTplName(sub_param), sub_param)}}',
		'                              </div>',
		'                           {{/if}}',
		'                              <span class="help-block">${sub_param.help}</span> <br />',
		'                           </div>',
		'                        {{/each}}',
		'                    {{/if}}',
		'                    </blockquote>',
		// if it's a single type
		'                {{else}}',
		'                    {{html getParameterDisplay(templates, getTplName(param), param)}}',
		'                    <span class="help-block">${param.help}</span>',
		'                {{/if}}',
		'                </div>',
		'            {{if group.indexOf("exclude-") == 0 && index == workflow.parameters_per_groups[group].length-1 }}',
		'                {{if group.indexOf("exclude-") == 0 }}',
		'                <div class="col-sm-1" style="padding:0">',
		'                  <div class="exclude-left">',
		'    				 <span class="input-group-btn btn-group-xs">',
		'      					<button id="prev_btn_${param.group}" class="btn btn-default" type="button"><span class="glyphicon glyphicon-chevron-left"></span>&nbsp;</button>',
		'    				 </span>',
		'                  </div>',
		'                  <div class="exclude-right">',
		'    				 <span class="input-group-btn btn-group-xs">',
		'      					<button id="next_btn_${param.group}" class="btn btn-default" type="button"><span class="glyphicon glyphicon-chevron-right"></span>&nbsp;</button>',
		'    				 </span>',
		'                  </div>',
		'                </div>',
		'                {{/if}}',
	    '            </div>',
	    '            {{else group.indexOf("exclude-") != 0}}',
	    '            </div>',
		'            {{/if}}',
		'            {{else}}',
		// if the param is already settled, hide it
		'              {{if param.action == "append"}}',
		'                <input id="${param.name}" name="${param.name}" value="${parameters[param.name].join(\"::-::\")}" type="hidden">',
		'              {{else}}',
		'                <input id="${param.name}" name="${param.name}" value="${parameters[param.name]}" type="hidden">',
		'              {{/if}}',
		'            {{/if}}',
		'        {{/each}}',
		'    </fieldset>',
		'    {{/each}}',
		'    <fieldset>',
		// for all workflow add the workflowClass
		'        <input name="workflow_class" value="${workflow.class}" type="hidden">',
		// add buttons if requested
		'        {{if display_reset_button || display_run_button}}',
	    '            <div class="row"> <div class="col-md-3 col-md-offset-9">',
		'                <div class="btn-group">',
		'                {{if display_reset_button}}',
		'                    <button id="wfform_reset_btn" type="button" class="btn btn-default"><span class="glyphicon glyphicon-refresh"></span> Reset</button>',
		'                {{/if}}',
		'                {{if display_run_button}}',
		'                    <button id="wfform_run_btn" type="button" class="btn btn-primary"><span class="glyphicon glyphicon-cog"></span> Run</button>',
		'                {{/if}}',
		'                </div>',
		'            </div>',
		'        {{/if}}',
		'    </fieldset>',
		'</form>',
		// add a second form for the files to upload
		'<form method="post" enctype="multipart/form-data" style="display:none;">',
		'  {{each(gindex, group) workflow.groups}}',
		'    {{each(index, param) workflow.parameters_per_groups[group]}}',
		// if param is an inputfile or just a browsefile
		'		{{if param.type.indexOf("inputfile") === 0 || param.type.indexOf("browsefile") === 0}}',
		'		  {{if param.action == "append"}}',
		'			<input name="browse_${param.name}" id="browse_${param.name}" class="fileupload" multiple type="file">',
		'		  {{else}}',
		'			<input name="browse_${param.name}" id="browse_${param.name}" class="fileupload" type="file">',
		'		  {{/if}}',
		// if it's a multiple type
		'       {{else param.type == "MultipleParameters"}}',
		'        {{each(spindex, sub_param) param.sub_parameters}}',
		'		   {{if sub_param.type.indexOf("inputfile") === 0 || sub_param.type.indexOf("browsefile") === 0}}',
		'	     	  {{if param.action == "append"}}',
		'			    <input name="browse_${sub_param.name}" id="browse_${sub_param.name}" multiple class="fileupload" type="file">',
		'		      {{else}}',
		'			    <input name="browse_${sub_param.name}" id="browse_${sub_param.name}" class="fileupload" type="file">',
		'		      {{/if}}',
		'		   {{/if}}',
		'        {{/each}}',			
		'		{{/if}}',
		'    {{/each}}',
		'  {{/each}}',
		'</form>',
		'<div id="progress"></div>'].join('\n');
	
	$.fn.wfform.defaults = {
		serverURL: "http://localhost:8080",
		dateTemplate: [
			'<div>', 
			'{{if param.action == "append"}}',
			'  <div id="date_${param.name}" class="input-group date list" data-date="${param.default}" data-date-multidate-separator=", " data-date-multidate="true" data-date-format="${param.format}">',
			'{{else}}',
			'  <div id="date_${param.name}" class="input-group date" data-date="${param.default}" data-date-format="${param.format}">',
			'{{/if}}',
			'    <input id="${param.name}" name="${param.name}" class="form-control" type="text" value="${param.default}">',
			'    <span class="input-group-btn">',
			'      <button class="btn btn-default" type="button"><span class="glyphicon glyphicon-calendar"></span>&nbsp;</button>',
			'    </span>',
			'  </div>',
			'</div>'
		].join('\n'),
		choiceTemplate: [
		    '<div>',
		    '{{if param.action == "append"}}', // if it's a multiple choice parameter, add a multiple select
		    '  <select id="${param.name}" multiple name="${param.name}" class="form-control list">',
		    '{{else}}', // if it's a single choice parameter, add a simple select
			'  <select id="${param.name}" name="${param.name}" class="form-control">',
			'{{/if}}',
			'  {{each(j, choice) param.choices}}',
			'    {{if choice == param.default}}',
			'    <option selected>${choice}</option>',
			'    {{else}}',
			'    <option>${choice}</option>',
			'    {{/if}}',
			'  {{/each}}',
			'  </select>',
		    '</div>'
		].join('\n'),
		inputfileTemplate: [
			'<div>',
			'  <div class="input-group">',
			'    <div class="input-group-btn">',
//			'      {{if param.action == "append"}}',
//			'      <button type="button" style="padding-top:23px; padding-bottom:22px;" class="btn btn-default dropdown-toggle" data-toggle="dropdown">',
//			'      {{else}}',
			'      <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">',
//			'      {{/if}}',
			'        <span id="inputfile_${param.name}">server file</span>',
			'        <span class="caret"></span>',
			'      </button>',
			'      <ul class="dropdown-menu" role="menu">',
			'        <li><a class="inputfile_${param.name}" href="#">server file</a></li>',
			'        {{if param.action == "append"}}',
            '        <li><a class="inputfile_${param.name}" href="#">server regexp</a></li>',
			'        {{/if}}',
			'        <li><a class="inputfile_${param.name}" href="#">local file</a></li>',
			'        <li><a class="inputfile_${param.name}" href="#">url</a></li>',
			'      </ul>',
			'    </div>',
			'    {{if param.action == "append"}}',
			'    <textarea id="${param.name}" style="resize:none" name="${param.name}" class="list form-control">${param.default.join("\n")}</textarea>',
			'    {{else}}',
			'    <input id="${param.name}" name="${param.name}" class="form-control" type="text" value="${param.default}">',
			'    {{/if}}',
			'    <span class="input-group-btn">',
//			'      {{if param.action == "append"}}',
//			'      <button id="urlfile_btn_${param.name}" style="display: none; padding-top:23px; padding-bottom:22px;" class="btn btn-default" type="button"><span class="glyphicon glyphicon-folder-open"></span>&nbsp;</button>',
//			'      {{else}}',
			'      <button id="urlfile_btn_${param.name}" style="display: none;" class="btn btn-default" type="button"><span class="glyphicon glyphicon-folder-open"></span>&nbsp;</button>',
//			'      {{/if}}',
			'    </span>',
			'  </div>',
		    '</div>'
		].join('\n'),
		browsefileTemplate: [
			'<div>',
			'  <div class="input-group">',
			'    {{if param.action == "append"}}',
			'    <textarea id="${param.name}" style="resize:none" name="${param.name}" class="list form-control to-readonly">${param.default.join("\n")}</textarea>',
			'    {{else}}',
			'    <input id="${param.name}" name="${param.name}" class="form-control to-readonly" type="text" value="${param.default}">',
			'    {{/if}}',
			'    <span class="input-group-btn">',
			'      <button id="urlfile_btn_${param.name}" class="btn btn-default" type="button"><span class="glyphicon glyphicon-folder-open"></span>&nbsp;</button>',
			'    </span>',
			'  </div>',
			'</div>'
		].join('\n'),
		regexpfilesTemplate: [
			'<div>',
			'  <textarea id="${param.name}" style="resize:none" name="${param.name}" class="list form-control">${param.default.join("\n")}</textarea>',
			'</div>'
		].join('\n'),
		booleanTemplate: [
			'<div>',
//			'  <div class="checkbox-inline">',
//			'    <label>',
			'    {{if param.default == true}}',
			'      <input id="${param.name}" name="${param.name}" value="${param.default}" type="checkbox" checked> ${check_title}',
			'    {{else}}',
			'      <input id="${param.name}" name="${param.name}" value="${param.default}" type="checkbox"> ${check_title}',
			'    {{/if}}',
//			'    </label>',
//			'  </div>',
			'</div>'
		].join('\n'),
		textTemplate: [
			'<div>',
		    '  {{if param.action == "append"}}',
			'    <textarea id="${param.name}" style="resize:none" name="${param.name}" class="list form-control">${param.default.join("\n")}</textarea>',
		    '  {{else}}',
			'    <input id="${param.name}" name="${param.name}" value="${param.default}" class="form-control" type="text">',
			'  {{/if}}',
			'</div>'
		].join('\n'),
		passwordTemplate:[
			'<div>',
			'    <input id="${param.name}" name="${param.name}" value="${param.default}" class="form-control" type="password">',
			'</div>'             
		].join('\n'),
		progressTemplate: ['<dl class="dl-horizontal">',
   		    '<div class="container-fluid"><div class="row"><div class="col-md-1 col-md-offset-2"><div class="inline floatingBarsG">',
            '<div class="blockG" id="rotateG_01"></div>',
            '<div class="blockG" id="rotateG_02"></div>',
            '<div class="blockG" id="rotateG_03"></div>',
            '<div class="blockG" id="rotateG_04"></div>',
            '<div class="blockG" id="rotateG_05"></div>',
            '<div class="blockG" id="rotateG_06"></div>',
            '<div class="blockG" id="rotateG_07"></div>',
            '<div class="blockG" id="rotateG_08"></div>',
            '</div></div> <div class="col-md-8">Please wait until all files have being loaded!</div></div>',
		    '<br/>',
		    '{{each(index, file) upload_file_status}}',
		    '<dt>${file.param}</dt>',
		    '<dd>',
		    '<div class="progress">',
		    '<div id="${file.param_id}_pbar" class="progress-bar progress-bar-success" role="progressbar" style="width: ${parseInt((file.loaded/file.total)*100)}%;"></div>',
		    '</div>',
		    '</dd>',
		    '{{/each}}',
		    '</dl>'].join('\n'),
		workflowClass: null,
		displayRunButton: true,
		displayResetButton: true,
		workflow: null,
		parameters: {},
		timer: 2000,
		forceIframeTransport: false
	}

	$.fn.wfform.Constructor = WFForm

}(window.jQuery);  