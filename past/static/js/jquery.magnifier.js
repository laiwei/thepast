/* jQuery Image Magnify script v1.1
* This notice must stay intact for usage 
* Author: Dynamic Drive at http://www.dynamicdrive.com/
* Visit http://www.dynamicdrive.com/ for full source code

* Nov 16th, 09 (v1.1): Adds ability to dynamically apply/reapply magnify effect to an image, plus magnify to a specific width in pixels.
* Feb 8th, 11 (v1.11): Fixed bug that caused script to not work in newever versions of jQuery (ie: v1.4.4)
*/

jQuery.noConflict()

jQuery.imageMagnify={
	dsettings: {
		magnifyby: 3, //default increase factor of enlarged image
		duration: 500, //default duration of animation, in millisec
		imgopacity: 0.2 //opacify of original image when enlarged image overlays it
 	},
	cursorcss: 'url(/static/css/magnify.cur), -moz-zoom-in', //Value for CSS's 'cursor' attribute, added to original image
	zIndexcounter: 100,

	refreshoffsets:function($window, $target, warpshell){
		var $offsets=$target.offset()
		var winattrs={x:$window.scrollLeft(), y:$window.scrollTop(), w:$window.width(), h:$window.height()}
		warpshell.attrs.x=$offsets.left //update x position of original image relative to page
		warpshell.attrs.y=$offsets.top
		warpshell.newattrs.x=winattrs.x+winattrs.w/2-warpshell.newattrs.w/2
		warpshell.newattrs.y=winattrs.y+winattrs.h/2-warpshell.newattrs.h/2
		if (warpshell.newattrs.x<winattrs.x+5){ //no space to the left?
			warpshell.newattrs.x=winattrs.x+5	
		}
		else if (warpshell.newattrs.x+warpshell.newattrs.w > winattrs.x+winattrs.w){//no space to the right?
			warpshell.newattrs.x=winattrs.x+5
		}
		if (warpshell.newattrs.y<winattrs.y+5){ //no space at the top?
			warpshell.newattrs.y=winattrs.y+5
		}
	},

	magnify:function($, $target, options){
		var setting={} //create blank object to store combined settings
		var setting=jQuery.extend(setting, this.dsettings, options)
		var attrs=(options.thumbdimensions)? {w:options.thumbdimensions[0], h:options.thumbdimensions[1]} : {w:$target.outerWidth(), h:$target.outerHeight()}
		var newattrs={}
		newattrs.w=(setting.magnifyto)? setting.magnifyto : Math.round(attrs.w*setting.magnifyby)
		newattrs.h=(setting.magnifyto)? Math.round(attrs.h*newattrs.w/attrs.w) : Math.round(attrs.h*setting.magnifyby)
		$target.css('cursor', jQuery.imageMagnify.cursorcss)
		if ($target.data('imgshell')){
			$target.data('imgshell').$clone.remove()
			$target.css({opacity:1}).unbind('click.magnify')
		}	
		var $clone=$target.clone().css({position:'absolute', left:0, top:0, visibility:'hidden', border:'1px solid gray', cursor:'pointer'}).appendTo(document.body)
		$clone.data('$relatedtarget', $target) //save $target image this enlarged image is associated with
		$target.data('imgshell', {$clone:$clone, attrs:attrs, newattrs:newattrs})
		$target.bind('click.magnify', function(e){ //action when original image is clicked on
			var $this=$(this).css({opacity:setting.imgopacity})
			var imageinfo=$this.data('imgshell')
			jQuery.imageMagnify.refreshoffsets($(window), $this, imageinfo) //refresh offset positions of original and warped images
			var $clone=imageinfo.$clone
			$clone.stop().css({zIndex:++jQuery.imageMagnify.zIndexcounter, left:imageinfo.attrs.x, top:imageinfo.attrs.y, width:imageinfo.attrs.w, height:imageinfo.attrs.h, opacity:0, visibility:'visible', display:'block'})
			.animate({opacity:1, left:imageinfo.newattrs.x, top:imageinfo.newattrs.y, width:imageinfo.newattrs.w, height:imageinfo.newattrs.h}, setting.duration,
			function(){ //callback function after warping is complete
				//none added		
			}) //end animate
		}) //end click
		$clone.click(function(e){ //action when magnified image is clicked on
			var $this=$(this)
			var imageinfo=$this.data('$relatedtarget').data('imgshell')
			jQuery.imageMagnify.refreshoffsets($(window), $this.data('$relatedtarget'), imageinfo) //refresh offset positions of original and warped images
			$this.stop().animate({opacity:0, left:imageinfo.attrs.x, top:imageinfo.attrs.y, width:imageinfo.attrs.w, height:imageinfo.attrs.h},  setting.duration,
			function(){
				$this.hide()
				$this.data('$relatedtarget').css({opacity:1}) //reveal original image
			}) //end animate
		}) //end click
	}
};

jQuery.fn.imageMagnify=function(options){
	var $=jQuery
	return this.each(function(){ //return jQuery obj
		var $imgref=$(this)
		if (this.tagName!="IMG")
			return true //skip to next matched element
		if (parseInt($imgref.css('width'))>0 && parseInt($imgref.css('height'))>0 || options.thumbdimensions){ //if image has explicit width/height attrs defined
			jQuery.imageMagnify.magnify($, $imgref, options)
		}
		else if (this.complete){ //account for IE not firing image.onload
			jQuery.imageMagnify.magnify($, $imgref, options)
		}
		else{
			$(this).bind('load', function(){
				jQuery.imageMagnify.magnify($, $imgref, options)
			})
		}
	})
};

jQuery.fn.applyMagnifier=function(options){ //dynamic version of imageMagnify() to apply magnify effect to an image dynamically
	var $=jQuery
	return this.each(function(){ //return jQuery obj
		var $imgref=$(this)
		if (this.tagName!="IMG")
			return true //skip to next matched element
		
	})	

};


//** The following applies the magnify effect to images with class="magnify" and optional "data-magnifyby" and "data-magnifyduration" attrs
//** It also looks for links with attr rel="magnify[targetimageid]" and makes them togglers for that image

jQuery(document).ready(function($){
	var $targets=$('.magnify')
	$targets.each(function(i){
		var $target=$(this)
		var options={}
		if ($target.attr('data-magnifyto'))
			options.magnifyto=parseFloat($target.attr('data-magnifyto'))
		if ($target.attr('data-magnifyby'))
			options.magnifyby=parseFloat($target.attr('data-magnifyby'))
		if ($target.attr('data-magnifyduration'))
			options.duration=parseInt($target.attr('data-magnifyduration'))
		$target.imageMagnify(options)
	})
	var $triggers=$('a[rel^="magnify["]')
	$triggers.each(function(i){
		var $trigger=$(this)
		var targetid=$trigger.attr('rel').match(/\[.+\]/)[0].replace(/[\[\]']/g, '') //parse 'id' from rel='magnify[id]'
		$trigger.data('magnifyimageid', targetid)
		$trigger.click(function(e){
			$('#'+$(this).data('magnifyimageid')).trigger('click.magnify')
			e.preventDefault()
		})
	})
})

