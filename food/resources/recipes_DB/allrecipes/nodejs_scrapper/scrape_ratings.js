const fs = require('fs');
const https = require('https')
const puppeteer = require('puppeteer');
const { PerformanceObserver, performance } = require('perf_hooks');

const n_trials_max = 5;

const page_size = 9;

function extractNumberOfReviews(){
	const extractElements = document.querySelectorAll('span.review-headline-count');
	const items = [];
	for (let element of extractElements) {	
		items.push(parseInt(element.innerText.replace( /[^\d.]/g, '' )));
	}
	return items;
}

function extractJSONReviewPage(){
	const elt = document.querySelectorAll('body');
	return elt;
}


function extractNReviewsFromMainRecipePage(){
	const elts = document.querySelectorAll('ul.ugc-ratings-list > li');
	return parseInt(elts[1].innerText.replace( /[^\d.]/g, '' ));
}

function extractItemsSinglePageEasy() {
	try{
		const extractFullReviewsElements = document.querySelectorAll('div.review-container');
		const items = [];
		var count = 0;
		for (let element of extractFullReviewsElements) {
			// items.push(element);
			// id
			const id = element.querySelectorAll('a')[0].href.split(".com")[1];
			// name
			const name = element.querySelectorAll('h4')[0].innerText.trim();
			//date
			const extractDate = element.querySelectorAll('div.review-date');
			var date = extractDate[0].innerText;
			// rating
			const extractRating = element.querySelectorAll('[itemprop=ratingValue]');
			var rating = extractRating[0].content;
			//review
			const extractReview = element.querySelectorAll('p');
			var review = extractReview[0].innerText;
			// if (extractReview.length > 0) review = extractReview[0].innerText.trim();
			// // new item
			const new_item = {"id": id, "name": name, "date": date, "rating": rating, "review": review};
			// if (rating != null && items.indexOf(new_item) == -1) items.push(new_item);
			items.push(new_item);
		}
		return items;
	} catch(e){
		console.log("Error extractItemsSinglePage");
		console.log(e);
	}
}

// ---------------------------------------------------------------------- //
//							Extract Ratings from page		    		  //
// ---------------------------------------------------------------------- //

function extractItemsSinglePage() {
	try{
		const extractFullReviewsElements = document.querySelectorAll('div.recipe-review-wrapper');
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


// ---------------------------------------------------------------------- //
//				Iterative calls if no answer to scrap reviews    		  //
// ---------------------------------------------------------------------- //

function enoughItems(items, n_min=12){
	return (items.length >= n_min);
}

async function extractItemsPageIdx(idx_page, page, url){
	try{
		const new_url = url + idx_page.toString();
		await page.goto(new_url);
		const items = await page.evaluate(extractItemsSinglePage);	
		if (! items) {
			console.log(0);
			return [];
		};
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

function isDictInList(d, l){
	for (let elt of l){
		if (elt['id'] == d['id']) return true;
	}
	return false;
}


async function extractItemsPages(idx_pasges_to_try, page, url, n_trials_max){
	const all_items = [];
	const cant_get_pages = [];

	for (let idx_page of idx_pasges_to_try){
		const items = await extractItemsPageIdxNTrials(idx_page, page, url, n_trials_max);
		if (enoughItems(items)){
			for (i of items){
				if (!isDictInList(i, all_items)) all_items.push(i);
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
//		Iterative calls if no answer to scrap number of reviews    		  //
// ---------------------------------------------------------------------- //


async function extractNumberOfReviewsNTrials(page, url, n_trials_max){
	var tried_n_times = 0;
	const new_url = url + '2';
	while (tried_n_times < n_trials_max){
		await page.goto(new_url);		
		const items = await page.evaluate(extractNumberOfReviews);	
		if (items.length > 0) return items[0];
	}
	return false;
}





async function mainExtractRatingsBad(page, url='https://www.allrecipes.com/recipe/19344/homemade-lasagna/?page='){
	console.log("Recipe", url);

	var start = performance.now();

	// get number of reviews to scrape
	const n_reviews = await extractNumberOfReviewsNTrials(page, url, n_trials_max);
	console.log("Reviews to scrap:", n_reviews);

	// get number of pages to scrape
	const n_pages = Math.ceil(n_reviews / 9);
	console.log("Pages to scrap:", n_pages);

	// generate list of pages to scrape
	const idx_pasges_to_try = [];
	for (var i=2; i<=n_pages; i++) idx_pasges_to_try.push(i);

	// scrape reviews from all pages
	const data = await extractItemsPages(idx_pasges_to_try, page, url, n_trials_max);
	const all_items = data["all_items"];
	const cant_get_pages = data['cant_get_pages'];

	// print number of elemts scraped and indexes of pages that failed
	try{
		console.log(all_items.length);
		console.log(cant_get_pages);
		// console.log(all_items);
	} catch(e) {
		console.log(e);
	}

	const new_all_items = [];
	if (cant_get_pages){
		// scrape pages that failed at first try
		const new_data = await extractItemsPages(cant_get_pages, page, url, n_trials_max);
		const new_all_items = data["all_items"];
		const new_cant_get_pages = data['cant_get_pages'];

		// print number of additional elements scraped and indexes of pages that failed
		try{
			console.log(new_all_items.length);
			console.log(new_all_items);
			console.log(new_cant_get_pages);
		} catch(e) {
			console.log(e);
		}
	}

	for (let e of new_all_items){
		all_items.push(e);
	}
	console.log("\nTotal:", all_items.length);
	console.log("Percentage:", all_items.length / n_reviews);

	var end = performance.now();
	console.log(end-start);
}

async function mainExtractRatings(page, rid='19344/homemade-lasagna'){
	var start = performance.now();

	// Get number of rivews to extract
	const main_recipe_page_url = 'https://www.allrecipes.com/recipe/'+rid;
	await page.goto(main_recipe_page_url);		
	const n_reviews = await page.evaluate(extractNReviewsFromMainRecipePage);	
	console.log("Number of reviews:", n_reviews);

	const n_pages = Math.ceil(n_reviews / page_size);
	console.log("Pages to scrap:", n_pages);

	// Extract reviews
	var page_idx = 0;
	const rid_number = rid.split("/")[0];
	const str1_reviewPage = 'https://www.allrecipes.com/recipe/getreviews/?recipeid='+rid_number+'&pagenumber='
	const str2_reviewPage = '&pagesize='+page_size.toString()+'&recipeType=Recipe&sortBy=MostHelpful';

	var n_reviews_collected = 0;
	const all_reviews = [];

	while (n_reviews_collected<n_reviews && page_idx<=n_pages){
		const url = str1_reviewPage + page_idx.toString() + str2_reviewPage;
		await page.goto(url);
		const json_reviews = await page.evaluate(extractItemsSinglePageEasy);
		console.log(page_idx, json_reviews.length);

		for (let item of json_reviews){
			if (!isDictInList(item, all_reviews)) all_reviews.push(item);
		}
		page_idx++;
		n_reviews_collected = all_reviews.length;

	}

	console.log("Total reviws:", n_reviews_collected);
	console.log("Percentage:", n_reviews_collected / n_reviews);

	var end = performance.now();
	console.log("Time (sec):", (end-start)/1000);

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

	// await mainExtractRatings(page);

	var contents = fs.readFileSync('recipes_to_scrap_allrecipes_all.json');
	var json_contents = JSON.parse(contents);
	// console.log(json_contents);





	// fs.writeFileSync('./reviews_test.txt', JSON.stringify(json_reviews));	

	for (let recipeid of json_contents){
		console.log(recipeid);
		await mainExtractRatings(page, recipeid);
	}
	

	await browser.close();

})();