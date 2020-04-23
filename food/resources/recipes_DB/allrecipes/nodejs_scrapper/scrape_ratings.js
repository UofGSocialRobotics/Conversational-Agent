const fs = require('fs');
const https = require('https')
const puppeteer = require('puppeteer');
const { PerformanceObserver, performance } = require('perf_hooks');

const n_trials_max = 5;

const page_size = 9;

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


function isDictInList(d, l){
	for (let elt of l){
		if (elt['id'] == d['id']) return true;
	}
	return false;
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