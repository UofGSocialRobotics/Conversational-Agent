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

function extractRecipe(){
	const title = document.querySelectorAll('div.headline-wrapper > h1')[0].innerText;
	// n ratings & reviews
	const elts = document.querySelectorAll('ul.ugc-ratings-list > li');
	const n_ratings = parseInt(elts[0].innerText.replace( /[^\d.]/g, '' ));
	const n_reviews = parseInt(elts[1].innerText.replace( /[^\d.]/g, '' ));
	// image url
	const imageExtract = document.querySelectorAll('div.image-container > div')[0];
	const key_str = Object.keys(imageExtract)[0];
	const image_url = imageExtract[key_str]['src'];
	// Time info
	const asideExtract = document.querySelectorAll('aside.recipe-info-section');
	const col1Extract = asideExtract[0].querySelectorAll('div.two-subcol-content-wrapper > div');
	var time_info = {};
	for (let elt of col1Extract){
		const header = elt.querySelectorAll('div.recipe-meta-item-header')[0].innerText.trim().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"");
		const value = elt.querySelectorAll('div.recipe-meta-item-body')[0].innerText.trim().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"");
		time_info[header] = value;
	}
	// Instructions
	const instructionsExtract = document.querySelectorAll('ul.instructions-section > li > div.section-body');
	const instructions = [];
	for (let elt of instructionsExtract){
		instructions.push(elt.innerText.trim());
	}
	// ingredients
	const ingredientsExtract = document.querySelectorAll('ul.ingredients-section > li.ingredients-item');
	const ingredients = [];
	for (let elt of ingredientsExtract){
		ingredients.push(elt.innerText.trim());
	}
	// send res
	const new_recipe = {
		"title": title, 
		"n_ratings":n_ratings, 
		"n_reviews":n_reviews, 
		"image_url": image_url, 
		"time_info": time_info, 
		"ingredients": ingredients,
		"instructions": instructions};
	return new_recipe;
}

function extractFullRecipeNutrition(){
	const caloriessplitted = document.querySelectorAll('div.recipe-nutrition > div')[0].innerText.trim().split(" ");
	const calories = parseInt(caloriessplitted[caloriessplitted.length - 1].replace( /[^\d.]/g, '' ));
	// nutrients
	const nutrientsExtract = document.querySelectorAll('div.nutrition-row');
	const nutrients = {};
	for (let elt of nutrientsExtract){
		const name_all = elt.innerText.trim();
		const value = elt.querySelectorAll('span.nutrient-value')[0].innerText.trim();
		const daily_value_extract = elt.querySelectorAll('span.daily-value');
		var daily_value = "";
		if (daily_value_extract[0]) {
			daily_value = daily_value_extract[0].innerText.trim();
		}
		const name = name_all.replace(value, "").replace(daily_value, "").trim();
		if (daily_value != ""){
			nutrients[name+" daily_value"] = daily_value;
		}
		nutrients[name] = value;
		if (daily_value != ""){
			nutrients[name+" daily_value"] = daily_value;
		}
	}
	// send res
	const full_nutrition = {
		"calories": calories,
		"nutrients": nutrients
	}
	return full_nutrition;
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

	} catch (e) {
		fs.appendFile('reviews_failed.txt', rid + "\n", function (err) {
			if (err) throw err;
			console.log('ERROR, could not collect reivews for recipe, saved recipe\'s id to reviews_failed.txt!');
		});
	}

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

	// read list of recipes to scrap
	var contents = fs.readFileSync('recipes_to_scrap_allrecipes_all.json');
	var json_contents = JSON.parse(contents);
	var idx_scraping = 0;
	var reviews_all_recipes = {};

	// read file of already scraped recipes
	const contents2 = fs.readFileSync('reviews_all_recipes.json');
	const json_already_scraped = JSON.parse(contents2);
	// get last index
	const index_stopped = Object.keys(json_already_scraped).length - 1;
	const key_stopped = Object.keys(json_already_scraped)[index_stopped];
	console.log("Last recipe scrapped:", key_stopped, json_contents[index_stopped], index_stopped, "\n");


	for (let recipeid of json_contents){

		if (idx_scraping > index_stopped){

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
			idx_scraping++;
		}

	}
	

	await browser.close();

})();