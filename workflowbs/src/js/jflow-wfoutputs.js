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

!function ($) {

	"use strict"; // jshint ;_;


	/* WFOutputs CLASS DEFINITION
	 * ========================= */

	var WFOutputs = function (element, options) {
		this.$element = $(element);
		this.options = $.extend({}, $.fn.wfoutputs.defaults, options);
		if (this.options.serverURL == "") { this.options.serverURL = $.fn.wfoutputs.defaults.serverURL; }
	}
	
	WFOutputs.prototype.reload = function() {
		var $this = this,
			params = "",
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
		if (this.options.workflowID) { params = "workflow_id=" + this.options.workflowID + "&"; }
		$.ajax({
		    url: this.options.serverURL + '/get_workflow_outputs?'+params+'callback=?',
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
		    	$this.$element.html("");
		    	$.tmpl($this.options.template, {data: data}).appendTo($this.$element);
		    	  	
		    	// Adding select options
		    	var extensions = new Array();
		    	$.each(data, function(i, component) {
		    		$.each(component, function(i, file) {
		    			if(	$.inArray( file.extension, extensions ) == -1 &&
		    				$.inArray( file.extension, $this.options.logFile ) == -1 ) {
		    					extensions.push(file.extension);
		    			}
		    		});
		    	});
		    	$.each(extensions, function(i, item) {
		    		$('#jflow_file_type').append($('<option>', {
		    			text: item
		    		}));
		    	});
		    	
		    	// Adding class for filters
		    	$(".output-file").each(function() {
		    		var fileExt = $(this).find("A").text().substr( ($(this).find("A").text().lastIndexOf('.') ) );
		    		if ($.inArray( fileExt, $this.options.logFile ) == -1 ) {
		    			$(this).addClass("output");
		    		}
		    		else {
		    			$(this).addClass("log");
		    			$(this).hide();
		    		}
		    	});
		    	
		    	// Events
		    	$("#jflow_log_on").click(function() {
		    		$(".log").each( function(){
		    			$(this).fadeIn(500);
		    		});
		    		$("#jflow_log_on").hide();
		    		$("#jflow_log_off").show();
		    	});
		    	$("#jflow_log_off").click(function() {
		    		$(".log").each( function(){
		    			$(this).fadeOut(500);
		    		});
		    		$("#jflow_log_off").hide();
		    		$("#jflow_log_on").show();
		    	});
		    	$("#jflow_file_type").on('change', function(){
		            var selected = $("#jflow_file_type option:selected").val();
		            var regex = new RegExp(selected);
		            $(".output").each( function(){
		            	if(selected == "all") {
		            		$(this).fadeIn(500);
		            	}
		            	else if( regex.test($(this).text())) {
		            		$(this).fadeIn(500);
		            	}
		            	else {
		            		$(this).fadeOut(500);
		            	}
		            });
		         });
		    }
    	});
	}
	
	/* WFOutputs PLUGIN DEFINITION
	 * ========================== */
	
	var old = $.fn.wfoutputs

	$.fn.wfoutputs = function (option) {
		return this.each(function () {
			var $this = $(this)
				, data = $this.data('wfoutputs')
				, options = $.extend({}, $.fn.wfoutputs.defaults, typeof option == 'object' && option)
				, action = typeof option == 'string' ? option : null
			// if already exist
			if (!data) $this.data('wfoutputs', (data = new WFOutputs(this, options)))
			// otherwise change the workflow
			else if (options.workflowID) { data.options.workflowID = options.workflowID; }
			if (action) { data[action]() }
			else { data.reload(); }
		})
	}

	$.fn.wfoutputs.defaults = {
		serverURL: "http://localhost:8080",
		template: ['<div style="float:right;margin-bottom:14px">',
		           '  <button id="jflow_log_on"  class="btn btn-default btn-xs" type="button"><span class="glyphicon glyphicon-eye-open"></span> View log files</button>',
		           '  <button id="jflow_log_off" style="display:none" class="btn btn-default btn-xs" type="button"><span class="glyphicon glyphicon-eye-close"></span> Mask log files</button>',
		           '  <span class="btn-xs">- View:</span>',
		           '  <select id="jflow_file_type" class="btn  btn-default btn-xs" style="width:auto">',
		           '   view: <option>all</option>',
		           '  </select><span class="btn-xs"> files.</span>',
		           '</div>',
		           '<div style="clear:both;">',
		           '  <dl "style=margin-bottom:15px">',
		           '  {{each(component_name, files) data}}',
		           '    <div style="clear:both"></div>',
		           '    <dt style="margin-top:15px;background-color: #eee">',
		           '      <span class="glyphicon glyphicon-play" style="color:white;left:-3px"></span>',
		           '      ${component_name}',
		           '    </dt>',
		           '    {{each(file_name, href) files}}',
		           '      <dd class="output-file" style="float:left;margin-left:20px;width:265px;overflow:hidden;white-space: nowrap;text-overflow:ellipsis;">',
		           '        <span class="glyphicon glyphicon-file"></span>',
		           '        <a href="${href.url}" download>${file_name}</a>',
		           '        <span style="color:grey">| ${href.size}</span>',
		           '      </dd>',
		           '    {{/each}}',
		           '  {{/each}}</dl>',
		           '</div>'].join('\n'),
		logFile: [".stderr", ".stdout", ".log"],
		workflowID: null
	}

	$.fn.wfoutputs.Constructor = WFOutputs

}(window.jQuery);  