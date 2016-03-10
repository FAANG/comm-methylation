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


	/* AvailableWF CLASS DEFINITION
	 * ========================= */

	var AvailableWF = function (element, options) {
		this.$element = $(element);
		this.options = $.extend({}, $.fn.availablewf.defaults, options);
		if (this.options.serverURL == "") { this.options.serverURL = $.fn.availablewf.defaults.serverURL; }
		this.reload();
	}
	
	AvailableWF.prototype.reload = function() {
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
		    url: this.options.serverURL + '/get_available_workflows?filter_groups=' + this.options.filter_groups.join(',') + '&select=' + this.options.select + '&callback=?',
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
		    	var workflow_by_class = {};
		    	for (var i in data) { 
		    		workflow_by_class[data[i]["class"]] = data[i]; 
		    	}
		    	$this.$element.html("");
		    	$.tmpl($this.options.template, {workflows: data, filters: $this.options.filters}).appendTo($this.$element);
		    	$("[id^=availablewf_btn_]").click(function(){
		    		var workflow_class = $(this).attr("id").split("availablewf_btn_")[1];
		    		$this.$element.trigger('select.availablewf', workflow_by_class[workflow_class]);
		    	});
		    }
    	});
	}
	
	/* AvailableWF PLUGIN DEFINITION
	 * ========================== */
	
	var old = $.fn.availablewf

	$.fn.availablewf = function (option) {
		return this.each(function () {
			var $this = $(this)
				, data = $this.data('availablewf')
				, options = $.extend({}, $.fn.availablewf.defaults, typeof option == 'object' && option)
				, action = typeof option == 'string' ? option : null
			if (!data) $this.data('availablewf', (data = new AvailableWF(this, options)))
			if (action) { data[action]() }
		})
	}

	$.fn.availablewf.defaults = {
		serverURL: "http://localhost:8080", 
		template: ['<table class="table table-striped table-striped">',
	        '<thead>',
		    '<tr>',
		    '<th>Name</th>',
			'<th>Description</th>',
		    '</tr>',
		    '</thead>',
		    '{{each(index, workflow) workflows}}',
		    // if this workflow shouldnt be displayed
			'  {{if filters.indexOf(workflow.class) == -1 }}',
		    '  <tr>',
			'    <td><a id="availablewf_btn_${workflow.class}" href="#">${workflow.name}</a></td>',
			'    <td>${workflow.help}</td>',
			'  </tr>',
			'  {{/if}}',
			'{{/each}}',
			'</dl>'].join('\n'),
		filters: [],
		filter_groups : [],
		select : false
	}

	$.fn.availablewf.Constructor = AvailableWF

}(window.jQuery);  