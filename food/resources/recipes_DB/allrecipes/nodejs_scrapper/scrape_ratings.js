const fs = require('fs');
const puppeteer = require('puppeteer');

// function extractItems() {
//   const extractedElements = document.querySelectorAll('li.cook-info > h4');
//   const items = [];
//   for (let element of extractedElements) {
//   	items.push(element.innerText);
//   }
//   return items;
// }
function getIntFromString(mystring){
	// str2 = mystring.replace ( /[^\d.]/g, '' );
	// return parseInt(str2);
	// return mystring;
	return 1;
}


function extractItemsSinglePage() {
	console.log("extractItemsSinglePage");
	try{
		const extractFullReviewsElements = document.querySelectorAll('div.recipe-review-wrapper');
		// const extractedElements = document.querySelectorAll('a.recipe-review-author');
		// const extractNames = document.querySelectorAll('span.reviewer-name');
		// const extractDates = document.querySelectorAll('span.recipe-review-date');
		// const extractRatings = document.querySelectorAll('span.review-star-text');
		// const extractReviews = document.querySelectorAll('p[prop=reviewBody]');
		const items = [];
		var count = 0;
		for (let element of extractFullReviewsElements) {
			console.log(element);
			// id
			const id = element.querySelectorAll('a.recipe-review-author')[0].href.split(".com")[1];
			// name
			const name = element.querySelectorAll('span.reviewer-name')[0].innerText.trim();
			//date
			const extractDate = element.querySelectorAll('span.recipe-review-date');
			var date = null;
			if (extractDate.length > 0) date = extractDate[0].innerText.trim();
			// rating
			const extractRating = element.querySelectorAll('span.review-star-text');
			var rating = null;
			if (extractRating.length > 0) rating = parseInt(extractRating[0].innerText.trim().replace( /[^\d.]/g, '' ));
			//review
			const extractReview = element.querySelectorAll('div.recipe-review-body');
			var review = null;
			if (extractReview.length > 0) review = extractReview[0].innerText.trim();
			// new item
			const new_item = {"id": id, "name": name, "date": date, "rating": rating, "review": review};
			if (rating != null && items.indexOf(new_item) == -1) items.push(new_item);
			// items.push(id);
		}
		return items;
	} catch(e){
		console.log("Error extractItemsSinglePage");
		console.log(e);
	}
}

function enoughItems(items, n_min=1){
	return (items.length >= n_min);
}

async function extractItemsPageIdx(idx_page, page, url){
	try{
		const new_url = url + idx_page.toString();
		await page.goto(new_url);
		const items = await page.evaluate(extractItemsSinglePage);	
		console.log(items.length);
		return items;
	} catch(e){
		console.log("Error extractItemsPageIdx");
		console.log(e);
	}
}

async function extractItemsPageIdxNTrials(idx_page, page, url, n_trials_max){
	try{
		console.log("Trying to extract from page", idx_page);
		var tried_n_times = 0;
		while(true){
			tried_n_times++;
			const items = await extractItemsPageIdx(idx_page, page, url);	
			enoughItemsBool = enoughItems(items);
			if(tried_n_times >= n_trials_max || enoughItemsBool) {
				return items;
			}
		}
	} catch(e){
		console.log("Error extractItemsPageIdxNTrials");
		console.log(e);
	}
}


async function extractItemsPages(idx_pasges_to_try, page, url, n_trials_max){
	const all_items = [];
	const cant_get_pages = [];

	for (let idx_page of idx_pasges_to_try){
		const items = await extractItemsPageIdxNTrials(idx_page, page, url, n_trials_max);
		if (enoughItems(items)){
			for (i of items){
				if (all_items.indexOf(i) == -1) all_items.push(i);
			}
		} else {
			console.log("Failed");
			cant_get_pages.push(idx_page);
		}
	}
	const data = {"all_items": all_items, "cant_get_pages": cant_get_pages};
	return data;	
}



// ---------------------------------------------------------------------- //
//								MAIN FUNCTION				    		  //
// ---------------------------------------------------------------------- //

(async () => {

	// Set up browser and page.
	const browser = await puppeteer.launch({
	headless: true,
	args: ['--no-sandbox', '--disable-setuid-sandbox'],
	});
	const page = await browser.newPage();
	page.setViewport({ width: 1280, height: 926 });

	// Navigate to the demo page.
	// url = 'https://www.allrecipes.com/recipe/255462/lasagna-flatbread'
	const url = 'https://www.allrecipes.com/recipe/19344/homemade-lasagna/?page='
	const n_pages = 2;
	const n_trials_max = 3;

	const idx_pasges_to_try = [];
	for (var i=2; i<=n_pages; i++) idx_pasges_to_try.push(i);

	console.log(idx_pasges_to_try);

	// const all_items = [];
	const data = await extractItemsPages(idx_pasges_to_try, page, url, n_trials_max);
	const all_items = data["all_items"];
	const cant_get_pages = data['cant_get_pages'];


	try{
		console.log(all_items.length);
		console.log(cant_get_pages);
		console.log(all_items);
	} catch(e) {
		console.log(e);
	}

	if (cant_get_pages){
		const new_data = await extractItemsPages(cant_get_pages, page, url, n_trials_max);
		const new_all_items = data["all_items"];
		const new_cant_get_pages = data['cant_get_pages'];


		try{
			console.log(new_all_items.length);
			console.log(new_cant_get_pages);
		} catch(e) {
			console.log(e);
		}
	}

	await browser.close();

})();