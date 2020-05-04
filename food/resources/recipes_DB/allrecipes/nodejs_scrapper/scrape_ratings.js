const fs = require('fs');
const https = require('https')
const puppeteer = require('puppeteer');
const { PerformanceObserver, performance } = require('perf_hooks');
// const lineReader = require('line-reader');
const lineByLine = require('n-readlines');


const n_trials_max = 5;

const page_size = 9;

const MAX_PAGES = 300;

const tooManyPages_file_path_json = 'reviews_too_many_pages.json';
const tooManyPages_file_path = 'reviews_too_many_pages.txt';

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
	try{

		const main_recipe_page_url = 'https://www.allrecipes.com/recipe/'+rid;
		console.log(main_recipe_page_url);
		await page.goto(main_recipe_page_url);		
		const n_reviews = await page.evaluate(extractNReviewsFromMainRecipePage);	
		console.log("Number of reviews:", n_reviews);

		const n_pages = Math.ceil(n_reviews / page_size);
		console.log("Pages to scrap:", n_pages);

		// if (n_pages >= MAX_PAGES){
		// 	fs.appendFile(tooManyPages_file_path, rid + "\n", function (err) {
		// 		if (err) throw err;
		// 		console.log('NO SCRAPING because too many reviews... Saved rid to ', tooManyPages_file_path);
		// 	});
		// }

		// else{

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
			setTimeout(function(){
				console.log("waited");
			}, 500);

		}

		console.log("Total reviews:", n_reviews_collected);
		const percentage = n_reviews_collected / n_reviews;
		console.log("Percentage:", percentage);

		const reviews_data = {
			"n_reviews_allrecipes": n_reviews,
			"n_reviews_collected": n_reviews_collected,
			"percentage": percentage,
			"reviews": all_reviews
		}

		var end = performance.now();
		console.log("Time (sec):", (end-start)/1000);

		return reviews_data;
		// return null;
		// }
		
	}catch (e) {
		fs.appendFile('reviews_failed.txt', rid + "\n", function (err) {
			if (err) throw err;
			console.log('ERROR, could not collect reivews for recipe, saved recipe\'s id to reviews_failed.txt!');
			console.log(rid);
			console.log(e);
		});
	}

}


// ---------------------------------------------------------------------- //
//					MAIN FUNCTION COLLECT ALL REVIEWS		    		  //
// ---------------------------------------------------------------------- //

async function mainCollectAll(){

	// Set up browser and page.
	const browser = await puppeteer.launch({
	headless: true,
	args: ['--no-sandbox', '--disable-setuid-sandbox'],
	});
	const page = await browser.newPage();
	page.setViewport({ width: 1280, height: 926 });

	// read list of recipes to scrap
	var contents = fs.readFileSync('recipes_to_scrap_allrecipes_all.json');
	var json_contents = JSON.parse(contents);
	var idx_scraping = 0;
	var reviews_all_recipes = {};

	// read file of already scraped recipes
	const contents2 = fs.readFileSync('reviews_all_recipes.json');
	const json_already_scraped = JSON.parse(contents2);
	const already_scraped_ids = Object.keys(json_already_scraped);


	for (let recipeid of json_contents){

		if (already_scraped_ids.indexOf(recipeid) == -1){

			console.log("\nIndex recipe:", idx_scraping);

			const reviews = await mainExtractRatings(page, recipeid);
			reviews_all_recipes[recipeid] = reviews;
			idx_scraping++;
			if(idx_scraping % 5 == 0 || idx_scraping == 1){
				console.log("wrote to file reviews_all_recipes.json");
				const to_save = {...json_already_scraped, ...reviews_all_recipes};
				fs.writeFileSync('./reviews_all_recipes.json', JSON.stringify(to_save));
			}
		}
		else {
			console.log("Passing: ", recipeid, idx_scraping++);
		}

	}
	

	await browser.close();

};

// ---------------------------------------------------------------------- //
//			MAIN FUNCTION COLLECT REVIEWS WITH > 300 PAGES	    		  //
// ---------------------------------------------------------------------- //

async function mainCollectTooManyPagesReviews() {

	// Set up browser and page.
	const browser = await puppeteer.launch({
	headless: true,
	args: ['--no-sandbox', '--disable-setuid-sandbox'],
	});
	const page = await browser.newPage();
	page.setViewport({ width: 1280, height: 926 });


	// read file of already scraped recipes
	const contents2 = fs.readFileSync('reviews_all_recipes.json');
	const json_already_scraped = JSON.parse(contents2);
	const already_scraped_ids = Object.keys(json_already_scraped);

	const too_many_pages_already_scraped = [];

	var idx_scraping = 0;
	var reviews_all_recipes = {};

	// read files with rids of recipes with too many pages
	const too_many_pages_contents = fs.readFileSync(tooManyPages_file_path_json);
	const json_too_many_pages = JSON.parse(too_many_pages_contents);

	for(let recipeid of json_too_many_pages){
	    console.log(recipeid);
	    if (already_scraped_ids.indexOf(recipeid) == -1 && too_many_pages_already_scraped.indexOf(recipeid) == -1){

			console.log("\nIndex recipe:", idx_scraping);

			const reviews = await mainExtractRatings(page, recipeid);
			reviews_all_recipes[recipeid] = reviews;
			idx_scraping++;
			// if(idx_scraping % 5 == 0 || idx_scraping == 1){
			console.log("wrote to file reviews_all_recipes.json");
			const to_save = {...json_already_scraped, ...reviews_all_recipes};
			fs.writeFileSync('./reviews_all_recipes.json', JSON.stringify(to_save));
			// }

			too_many_pages_already_scraped.push(recipeid);
		}
		else {
			console.log("Passing: ", recipeid, idx_scraping++);
		}
	}

	await browser.close();

};



// ---------------------------------------------------------------------- //
//									MAIN 					    		  //
// ---------------------------------------------------------------------- //

(async () => {
	await mainCollectTooManyPagesReviews();
	// await mainCollectAll();
})();